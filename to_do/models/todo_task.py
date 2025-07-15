from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class TodoTask(models.Model):
    _name = 'todo.task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Task"

    name = fields.Char('Task Name')
    due_date = fields.Date()
    description = fields.Text()
    assign_to_id = fields.Many2one('res.partner')
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], default='new')
    partner_id = fields.Many2one('res.partner', string="Partner")

    certification_ids = fields.One2many(
        comodel_name='partner.certification',
        inverse_name='partner_id',
        string='Certifications',
        compute='_compute_certifications',
        store=False,
    )

    @api.depends('assign_to_id')
    def _compute_certifications(self):
        for rec in self:
            if rec.assign_to_id:
                rec.certification_ids = self.env['partner.certification'].search([
                    ('partner_id', '=', rec.assign_to_id.id)
                ])
            else:
                rec.certification_ids = False

    def action_in_progress(self):
        self.state = 'in_progress'

    def action_new(self):
        self.state = 'new'

    def action_completed(self):
        self.state = 'completed'


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    min_price = fields.Float(string="Minimum Sale Price")
    max_price = fields.Float(string="Maximum Sale Price")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_price_exceed_limit = fields.Boolean(compute='_compute_price_limit', store=False)
    is_price_valid = fields.Boolean(compute='_compute_price_limit', store=False)
    min_price = fields.Float(string="Minimum Price")
    max_price = fields.Float(related='product_id.max_price', string="Max Price", store=False, readonly=True)

    @api.depends('price_unit', 'product_id.min_price', 'product_id.max_price')
    def _compute_price_limit(self):
        for line in self:
            min_p = line.product_id.min_price
            max_p = line.product_id.max_price
            if min_p and max_p:
                line.is_price_valid = min_p <= line.price_unit <= max_p
                line.is_price_exceed_limit = not line.is_price_valid
            else:
                line.is_price_valid = True
                line.is_price_exceed_limit = False


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    approval_stage = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('first_approved', 'First Approved'),
        ('second_approved', 'Second Approved'),
        ('final_approved', 'Final Approved'),
    ], string='Approval Stage', default='draft', tracking=True)

    approval_detail_ids = fields.One2many('approval.detail', 'sale_order_id', string='Approvals')
    current_approval_level = fields.Integer(string='Current Level', default=0)

    def action_approve(self):
        for order in self:
            next_level = order.current_approval_level + 1
            next_steps = order.approval_detail_ids.filtered(lambda l: l.level == next_level)

            if not next_steps:
                raise UserError(_("No further approval levels."))

            for step in next_steps:
                if step.min_amount and order.amount_total < step.min_amount:
                    continue

                if step.approve_by == 'user':
                    if self.env.user != step.user_id:
                        raise UserError(_("You are not authorized to approve this level."))
                elif step.approve_by == 'group':
                    if step.group_id not in self.env.user.groups_id:
                        raise UserError(_("Your group is not authorized to approve this level."))

            order.current_approval_level = next_level
            if next_level == max(order.approval_detail_ids.mapped('level')):
                order.approval_stage = 'final_approved'
            else:
                order.approval_stage = 'in_progress'

    def action_confirm(self):
        for order in self:
            for line in order.order_line:
                product = line.product_id
                if product.min_price and line.price_unit < product.min_price:
                    if not self.env.user.has_group('app_one.group_allow_confirm_order'):
                        raise ValidationError("لا يمكنك تأكيد الطلب لأن السعر أقل من الحد الأدنى.")
                if product.max_price and line.price_unit > product.max_price:
                    if not self.env.user.has_group('app_one.group_allow_confirm_order'):
                        raise ValidationError("لا يمكنك تأكيد الطلب لأن السعر أعلى من الحد الأقصى.")
        return super().action_confirm()

    def action_first_approve(self):
        for order in self:
            order.approval_stage = 'first_approved'

    def action_second_approve(self):
        for order in self:
            if order.approval_stage != 'first_approved':
                raise UserError(_("First approval required."))
            if not self.env.user.has_group('to_do.group_approve_second'):
                raise UserError(_("You are not allowed to approve at this stage."))
            order.approval_stage = 'second_approved'

    def action_final_approve(self):
        for order in self:
            if order.approval_stage != 'second_approved':
                raise UserError(_("Second approval required."))
            if not self.env.user.has_group('to_do.group_approve_final'):
                raise UserError(_("You are not allowed to approve at this stage."))
            order.approval_stage = 'final_approved'


class ApprovalDetail(models.Model):
    _name = 'approval.detail'
    _description = 'Approval Detail'
    _order = 'level asc'

    level = fields.Integer(required=True)
    approve_by = fields.Selection([
        ('user', 'User'),
        ('group', 'Group'),
    ], required=True)
    user_id = fields.Many2one('res.users')
    group_id = fields.Many2one('res.groups')
    min_amount = fields.Float(string='Min Total Amount')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade')

    @api.constrains('level', 'sale_order_id')
    def _check_unique_level(self):
        for rec in self:
            domain = [('sale_order_id', '=', rec.sale_order_id.id), ('level', '=', rec.level)]
            if rec.id:
                domain.append(('id', '!=', rec.id))
            if self.env['approval.detail'].search_count(domain):
                raise ValidationError(_('Level must be unique per order.'))

    @api.onchange('approve_by')
    def _onchange_approve_by(self):
        if self.approve_by == 'user':
            self.group_id = False
        else:
            self.user_id = False




class PartnerCertification(models.Model):
    _name = 'partner.certification'
    _description = 'Partner Certification'

    name = fields.Char("Certification Name", required=True)
    validation_from = fields.Date("Valid From")
    validation_to = fields.Date("Valid To")
    attachment = fields.Binary("Attachment")
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')



class ResPartner(models.Model):
    _inherit = 'res.partner'

    certification_ids = fields.One2many('partner.certification', 'partner_id', string="Certifications")




class AccountMove(models.Model):
    _inherit = 'account.move'


    def action_view_delivery_orders(self):
        self.ensure_one()
        if not self.invoice_origin:
            raise UserError("No source sale order linked to this invoice.")

        sale_orders = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        if not sale_orders:
            raise UserError("No sale order found linked to this invoice.")

        pickings = sale_orders.mapped('picking_ids')
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        if len(pickings) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action['domain'] = [('id', 'in', pickings.ids)]

        return action


# models/sale_order_excel_wizard.py
from odoo import models, fields, api
from odoo import models
import io
from datetime import datetime
import xlsxwriter



class SaleOrderExcelWizard(models.TransientModel):
    _name = 'sale.order.excel.wizard'
    _description = 'Wizard to Export Sale Orders to Excel'

    order_ids = fields.Many2many('sale.order', string='Sale Orders')
    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')

    def action_export_excel(self):
        return self.env.ref('to_do.sale_order_excel_report_action').report_action(self)




class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_picking_type_ids = fields.Many2many(
        'stock.picking.type',
        'res_users_stock_picking_type_rel',
        'user_id',
        'picking_type_id',
        string='Allowed Picking Types'
    )

class ProductCategory(models.Model):
    _inherit = 'product.category'

    sequence_per_category = fields.Integer(string='Category Sequence', default=1)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    custom_name_with_category = fields.Char(string="اسم مخصص تلقائي", readonly=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.categ_id:
            seq = record.categ_id.sequence_per_category
            record.custom_name_with_category = f"{record.name} / {record.categ_id.name} / {seq:03d}"
            record.categ_id.sequence_per_category += 1

        return record

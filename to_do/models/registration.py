from odoo import models, fields, api

class PartnerCertification(models.Model):
    _name = 'partner.certification'
    _description = 'Partner Certification'

    name = fields.Char(string="Certificate Name", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    validation_from = fields.Date(string="Valid From")
    validation_to = fields.Date(string="Valid To")
    attachment = fields.Binary(string="Attachment", attachment=True)


class PartnerRegistration(models.Model):
    _name = 'partner.registration'
    _description = 'Partner Registration'

    name = fields.Char(string="Registration Name", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)

    certification_ids = fields.One2many(
        comodel_name='partner.certification',
        inverse_name='partner_id',
        string='Certifications',
        compute='_compute_certifications',
        store=False,
    )

    @api.depends('partner_id')
    def _compute_certifications(self):
        for rec in self:
            if rec.partner_id:
                rec.certification_ids = self.env['partner.certification'].search([
                    ('partner_id', '=', rec.partner_id.id)
                ])
            else:
                rec.certification_ids = False

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError

class ProjectConstructiontLine(models.Model):
    _name = 'project.construct.line'
    _description = 'Project Constructiont Line'

    project_id = fields.Many2one('project.project')
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    pre_construct_price = fields.Float(string="Pre Construction Price")
    under_construct_price = fields.Float(string="Under Construction Price")
    post_construct_price = fields.Float(string="Post Construction Price")

    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id


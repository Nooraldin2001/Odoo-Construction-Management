from odoo import models, fields, api

class MaterialPlanning(models.Model):
    _name = 'material.plan'
    _description = 'Material Plan'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        self.description = self.product_id.name

    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_uom_qty = fields.Integer(string='Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    material_task_id = fields.Many2one('project.task', string='Material Plan Task')


class ConsumedMaterial(models.Model):
    _name = 'consumed.material'
    _description = 'Consumed Material'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        self.description = self.product_id.name

    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_uom_qty = fields.Integer(string='Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    consumed_task_material_id = fields.Many2one('project.task', string='Consumed Material Plan Task')
    is_picked = fields.Boolean()
    consumed_qty = fields.Float()

from odoo import api, fields, models, _


class ConstructCycle(models.Model):
    _name = 'construct.cycle'
    _description = "Cycles"

    name = fields.Char(string="Name")
    process_ids = fields.Many2many('construct.process', string="Process")

class ConstructProcess(models.Model):
    _name = 'construct.process'
    _description = "Process"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    hours = fields.Float()
    description = fields.Text()
    prces_material_ids = fields.One2many('construct.process.material','construct_process_id', string="Process Materials")
    equipment_ids = fields.Many2many('maintenance.equipment', string="Equipments")
    fleet_ids = fields.Many2many('fleet.vehicle', string="Fleet")

class ConstructProcessMaterial(models.Model):
    _name = 'construct.process.material'
    _description = "Construct Process Material"

    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    price = fields.Float(string="Price")
    sub_total = fields.Float(string='Sub total', compute="_compute_sub_total")
    construct_process_id = fields.Many2one('construct.process', string="Construct Process")
    project_task_id = fields.Many2one('project.task', string="Task")

    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
            rec.price = rec.product_id.lst_price

    @api.depends('price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.qty
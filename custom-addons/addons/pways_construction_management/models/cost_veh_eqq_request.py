from datetime import date
from odoo import models, fields, api, _

class VehicleEquipmentRequest(models.Model):
    _name = 'vehicle.equipment.request'
    _description = 'Vehicle Equipment Request'
    _order = "id desc"
    
    name = fields.Char(readonly=True)
    hours = fields.Float()
    description = fields.Text()
    request_type = fields.Selection(selection=[('vehicle','Vehicle'),('equipment','Equipment')], string='Type', default='vehicle')
    equipment_ids = fields.Many2many('maintenance.equipment', string="Equipments")
    fleet_ids = fields.Many2many('fleet.vehicle', string="Fleet")
    task_id = fields.Many2one('project.task', string="Task")
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('cancel', 'Canceled')], string='State', tracking=True, default='draft')
    # state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'), ('done', 'Done'), ('cancel', 'Canceled')], string='State', tracking=True, default='draft')

    def action_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirm'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    @api.model
    def create(self, vals):
        if vals.get('request_type') == 'vehicle':
            prefix = 'FLT/REQ/'
        else:
            prefix = 'EQP/REQ/'

        seq_number = self.env['ir.sequence'].next_by_code('vehicle.equipment.request') or 'New'
        vals['name'] = f"{prefix}{seq_number}"

        return super(VehicleEquipmentRequest, self).create(vals)

    def write(self, vals):
        # Prevent changing the request_type by removing it from vals
        if 'request_type' in vals:
            del vals['request_type']
        return super(VehicleEquipmentRequest, self).write(vals)
from odoo import api, fields, models, _
from datetime import datetime, date

class ConstructInspector(models.Model):
    _name = 'construct.inspector'
    _description = "construct Inspector"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name",default='New')
    inspector_id = fields.Many2one('res.users', string="Inspector" ,default=lambda self: self.env.user)
    project_id = fields.Many2one('project.project', string="Project",required=True)
    task_id = fields.Many2one('project.task', string="Task",required=True)
    date = fields.Date(default=fields.Date.today())
    description = fields.Text(string="Description")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Submit'), ('cancel', 'Cancel')], default="draft")
    attachment_ids = fields.Many2many('ir.attachment')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('construct.inspector') or 'New'
        return super(ConstructInspector, self).create(vals)

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_reset(self):
        self.state = "draft"

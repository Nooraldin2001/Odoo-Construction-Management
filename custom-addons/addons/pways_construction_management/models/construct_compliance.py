from odoo import api, fields, models, _
from datetime import datetime, date

class ConstructCompliance(models.Model):
    _name = 'construct.compliance'
    _description = "Construct Compliance"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default='New')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    project_id = fields.Many2one('project.project', required=True)
    task_id = fields.Many2one('project.task', required=True)
    confirm_date = fields.Date()
    approval_date = fields.Date()
    submit_date = fields.Date()
    aprv_govt_date = fields.Date()
    description = fields.Text()
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'), ('submit', 'Submit'), ('done', 'Approved By Govt.'), ('cancel', 'Cancel')], default="draft")
    attachment_ids = fields.Many2many('ir.attachment')
    cnstrct_cmpln_tags_ids = fields.Many2many('construct.compliance.tags', string="Construct Compliance Tags")
    site_name = fields.Char()
    site_length = fields.Float()
    site_width = fields.Float()
    site_area = fields.Float()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('construct.compliance') or 'New'
        return super(ConstructCompliance, self).create(vals)

    def action_draft(self):
        self.state = "draft"

    def action_confirm(self):
        self.confirm_date = date.today()
        self.state = "confirm"

    def action_approve(self):
        self.approval_date = date.today()
        self.state = "approve"
        
    def action_submit(self):
        self.submit_date = date.today()
        self.state = "submit"

    def action_done(self):
        self.aprv_govt_date = date.today()
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'
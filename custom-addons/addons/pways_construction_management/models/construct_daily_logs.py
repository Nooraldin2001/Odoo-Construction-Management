from odoo import api, fields, models, _
from datetime import datetime, date

class ConstructionDailyLogs(models.Model):
    _name = 'construct.daily.logs'
    _description = "Construction Daily Logs"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", compute="_compute_name", copy=False)
    date = fields.Date(string="Date", default=fields.Date.today())
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    parent_id = fields.Many2one('hr.employee', string="Manager")
    department_id = fields.Many2one('hr.department', string='Department',)
    project_id = fields.Many2one('project.project', string='Project')
    job_costing_id = fields.Many2one('job.costing', related="project_id.job_cost_id", string="Job Costing")
    analytic_account_id = fields.Many2one('account.analytic.account', related="project_id.analytic_account_id", string='Analytic Account')
    task_ids = fields.Many2many('project.task', string="Task")
    cnstrct_daily_logs = fields.Html(string="Construction Daily Logs")
    cnstrct_subcontractors = fields.Html(string="Subcontractors")
    cnstrct_activities = fields.Html(string="Activities")
    cnstrct_test = fields.Html(string="Test/Inspection")
    cnstrct_eqquipment = fields.Html(string="Eqquipment")
    cnstrct_material_delivery = fields.Html(string="Material Delivries")
    cnstrct_visitors = fields.Html(string="Visitors")
    cnstrct_notes = fields.Html(string="Notes")

    @api.depends('date', 'user_id')
    def _compute_name(self):
        for rec in self:
            if rec.user_id and rec.date:
                rec.name = f"{rec.user_id.name} - {rec.date.strftime('%Y-%m-%d')}"
            else:
                rec.name = '/'

    def send_to_manager(self):
        self.ensure_one()
        template_id = self.env.ref('pways_construction_management.email_temp_construct_daily_logs')
        ctx = {
            'default_model': 'construct.daily.logs',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id if template_id else None,
            'default_composition_mode': 'comment',
            'force_email': True,
            'email_to': self.parent_id.work_email,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
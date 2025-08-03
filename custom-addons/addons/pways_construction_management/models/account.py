from odoo import models, fields

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    equipment_ids = fields.Many2many('maintenance.equipment', string="Equipments")
    account_analytic_line_id = fields.Many2one('account.analytic.line')
    maintenance_request_id = fields.Many2one('maintenance.request')
    task_id = fields.Many2one('project.task', string='Project Task')
    project_id = fields.Many2one('project.project', string='Project')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)

class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)
    job_cost_line_id = fields.Many2one('job.cost.line', string='Job Cost Line',)

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    start_time = fields.Float(string='Start Time',)
    end_time = fields.Float(string='End Time',)
    job_cost_id = fields.Many2one('job.costing',string='Job Cost Center',)
    job_cost_line_id = fields.Many2one('job.cost.line',string='Job Cost Line',)
    is_billed = fields.Boolean()
    is_from_task = fields.Boolean()

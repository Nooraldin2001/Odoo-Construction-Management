from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import Warning

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    custom_requisition_id = fields.Many2one('material.purchase.requisition',string='Purchase Requisition',readonly=True,copy=True)
    maintenance_request_id = fields.Many2one('maintenance.request')
    task_id = fields.Many2one('project.task', string='Project Task')
    project_id = fields.Many2one('project.project')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    custom_requisition_line_id = fields.Many2one('material.purchase.requisition.line',string='Requisitions Line',copy=True)
    task_id = fields.Many2one('project.task',string='Project Task')
    project_id = fields.Many2one('project.project')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)

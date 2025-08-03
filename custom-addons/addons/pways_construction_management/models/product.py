from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

################## Product ##################

class Product(models.Model):
    _inherit = 'product.product'

    boq_type = fields.Selection([('eqp_machine', 'Machinery / Material'), ('worker_resource', 'Worker / Resource'), ('work_cost_package', 'Work Cost Package'), ('subcontract', 'Subcontract')],  string='BOQ Type',)

################## Maintenance Equipment ##################

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    task_id = fields.Many2one('project.task', string='Project Task')
    product_id = fields.Many2one('product.product', string='Product')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center')


################## HR ##################

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    task_id = fields.Many2one('project.task', string='Task')
    project_id = fields.Many2one('project.project', related="task_id.project_id", string='Project', readonly=False)
    job_cost_id = fields.Many2one('job.costing', related="task_id.job_cost_id", string='Job Cost Center')

    def _get_default_expense_sheet_values(self):
        values = super(HrExpense, self)._get_default_expense_sheet_values()
        for val in values:
            val.update({
                'project_id': self.project_id.id if self.project_id else False,
                'task_id': self.task_id.id if self.task_id else False,
                'job_cost_id': self.job_cost_id.id if self.job_cost_id else False,
            })
        return values

        
    def _prepare_move_line_vals(self):
        values = super(HrExpense, self)._prepare_move_line_vals()
        values.update({
            'job_cost_id': self.job_cost_id.id if self.job_cost_id else False,
        })
        return values

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    task_id = fields.Many2one('project.task', string='Task')
    project_id = fields.Many2one('project.project', related="task_id.project_id", string='Project', readonly=False)
    job_cost_id = fields.Many2one('job.costing', related="task_id.job_cost_id", string='Job Cost Center')

    def _prepare_bill_vals(self):
        values = super(HrExpenseSheet, self)._prepare_bill_vals()
        values.update({
            'project_id': self.project_id.id if self.project_id else False,
            'task_id': self.task_id.id if self.task_id else False,
            'job_cost_id': self.job_cost_id.id if self.job_cost_id else False,
        })
        return values


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dest_location_id = fields.Many2one('stock.location', string='Destination Location', groups='hr.group_hr_user')
    price_per_time = fields.Float(string='Salary/Time',)
    salary_period = fields.Selection(selection=[('hours', 'Hours'), ('days', 'Days'), ('months', 'Months')],  default="hours", string='Salary Period')

class HrEmployee(models.Model):
    _inherit = 'hr.department'

    dest_location_id = fields.Many2one('stock.location', string='Destination Location')

################## Project Task Type ##################

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    set_default = fields.Boolean('Default?')
    progress_bar = fields.Float(string='Progress (%)', help='Set your progress of the stage')
    is_progress_stage = fields.Boolean(string='Is Progress Bar', help='You can only see the progress ' 'if you enable this ')

    @api.constrains('progress_bar', 'sequence')
    def project_progress_bar(self):
        """The Constraints for the project Task Type Model"""
        all_progress = self.search([('is_progress_stage', '=', True), ('id', '!=', self.id)])
        records = {}
        for rec in all_progress:
            records[rec.progress_bar] = rec.sequence
        if self.progress_bar in records.keys():
            raise UserError(_("Ensure that the progress is not duplicated."))
        for rec in self.env['project.task.type'].search([]).filtered(
                lambda progress: progress.is_progress_stage == True and progress.id != self.id).mapped(
            'progress_bar'):
            value = [line for line in records if line == rec]
            if self.progress_bar < rec:
                if float(self.sequence) >= records[value[0]]:
                    raise UserError(
                        _(" The progress in this stage must greater than that"
                          " of the other stages progress bars. Alternatively,"
                          " reassess the priority assigned to this stage."))
                else:
                    continue
            else:
                if float(self.sequence) < records[value[0]]:
                    raise UserError(
                        _(" The progress in this stage must less than that of"
                          " the other stages progress bars. Alternatively,"
                          " reassess the priority assigned to this stage."))
                else:
                    continue
        if self.progress_bar > 100:
            raise UserError(_(" The progress must be less than or equal to 100"))

################## Res Partner ##################

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_farm_stats(self):
        job_costing_count = self.env['job.costing'].sudo().search_count([('user_id', '=', self.env.user.id)])
        projects_count = self.env['project.project'].sudo().search_count([('user_id', '=', self.env.user.id)])
        tasks_count = self.env['project.task'].sudo().search_count([('project_id', '!=', False), ('user_ids', 'in', self.env.user.id)])
        contractors_count = self.env['res.partner'].sudo().search_count([])
        bills_count = self.env['account.move'].sudo().search_count(['|', '|', ('project_id', '!=', False), ('task_id', '!=', False), ('job_cost_id', '!=', False)])
        picking_count = self.env['stock.picking'].sudo().search_count(['|', '|', ('project_id', '!=', False), ('task_id', '!=', False), ('job_cost_id', '!=', False)])
        inspection_count = self.env['construct.inspector'].sudo().search_count([('inspector_id', '=', self.env.user.id)])
        compliance_count = self.env['construct.compliance'].sudo().search_count([('user_id', '=', self.env.user.id)])
        materials_count = self.env['product.product'].sudo().search_count([])
        purchase_count = self.env['material.purchase.requisition'].sudo().search_count([('requisition_type', '=', 'purchase'), ('task_user_ids', 'in', self.env.user.id)])
        in_picking_count = self.env['material.purchase.requisition'].sudo().search_count([('requisition_type', '=', 'internal'), ('task_user_ids', 'in', self.env.user.id)])
        scraps_count = self.env['material.purchase.requisition'].sudo().search_count([('requisition_type', '=', 'scrap'), ('task_user_ids', 'in', self.env.user.id)])

        data = {
            'job_costing_count': job_costing_count,
            'projects_count': projects_count,
            'tasks_count': tasks_count,
            'contractors_count': contractors_count,
            'bills_count': bills_count,
            'picking_count': picking_count,
            'inspection_count': inspection_count,
            'compliance_count': compliance_count,
            'materials_count': materials_count,
            'purchase_count': purchase_count,
            'in_picking_count': in_picking_count,
            'scraps_count': scraps_count,
            }
        return data    

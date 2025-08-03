from datetime import date, timedelta
from odoo import fields, http
from odoo.http import request
from collections import defaultdict

class ConstructDashboard(http.Controller):
    @http.route('/construct/dashboard', type='json', auth='user')
    def _get_agri_dashboard_values(self):
        company_id = request.env.user.company_id
        current_year = date.today().year

        # Fetch invoices related to projects for the current year
        invoices = request.env['account.move'].search([
            # ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', f'{current_year}-01-01'),
            ('invoice_date', '<=', f'{current_year}-12-31'),
            ('project_id', '!=', False),
        ])

        # Prepare data for the yearly invoices chart with month abbreviations
        project_invocie_yearly = [['Month', 'Total Invoices']]
        for month in range(1, 13):
            monthly_total = sum(invoice.amount_total for invoice in invoices if invoice.invoice_date.month == month)
            month_name = date(current_year, month, 1).strftime("%b")
            project_invocie_yearly.append([month_name, monthly_total])

        # Project data
        projects = request.env['project.project'].search([
            ('company_id', '=', company_id.id),
            ('date_start', '>=', f'{current_year}-01-01'),
            ('date', '<=', f'{current_year}-12-31'),
        ])

        project_state_data = [['State', 'Projects']]
        state_count = defaultdict(int)
        for project in projects:
            state_count[project.state] += 1

        for state, count in state_count.items():
            project_state_data.append([state, count])

        # Task data
        tasks = request.env['project.task'].search([
            ('company_id', '=', company_id.id),
            ('create_date', '>=', f'{current_year}-01-01'),
            ('create_date', '<=', f'{current_year}-12-31'),
        ])

        task_stage_data = [['Stage', 'Tasks']]
        stage_count = defaultdict(int)
        for task in tasks:
            stage_name = task.stage_id.name if task.stage_id else 'Undefined'
            stage_count[stage_name] += 1

        for stage, count in stage_count.items():
            task_stage_data.append([stage, count])

        # Get all job costing records for the current year
        job_costings = request.env['job.costing'].search([
            ('create_date', '>=', f'{current_year}-01-01'),
            ('create_date', '<=', f'{current_year}-12-31'),
            ('company_id', '=', company_id.id),
        ])

        # Aggregate the total cost by job type
        cost_by_job_type = defaultdict(float)

        for job in job_costings:
            # Get the amount based on the job type
            cost_by_job_type['material'] += job.cost_material_total_price
            cost_by_job_type['labour'] += job.cost_labours_total_price
            cost_by_job_type['overhead'] += job.cost_overheads_total_price
            cost_by_job_type['vehicle'] += job.cost_fleet_total_price
            cost_by_job_type['equipment'] += job.cost_equipment_total_price

        # Prepare data for the graph
        cost_type_data = [['Job Type', 'Total Cost']]
        for job_type, total_cost in cost_by_job_type.items():
            cost_type_data.append([job_type.capitalize(), total_cost])
        data = {
            'project_state_data': project_state_data,
            'task_stage_data': task_stage_data,
            'project_invocie_yearly': project_invocie_yearly,
            'cost_type_estimated_amount_yearly': cost_type_data,
        }
        return data

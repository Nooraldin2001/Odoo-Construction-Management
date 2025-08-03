from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class TimesheetBillWizard(models.TransientModel):
    _name = 'timesheet.bill.wizard'

    timesheet_bill_wiz_lines = fields.One2many('timesheet.bill.wizard.line', 'timesheet_bill_wiz_id')

    @api.model
    def default_get(self, fields):
        res = super(TimesheetBillWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        company_id = self.env.user.company_id
        account_analytic_list = []
        if active_ids:
            account_analytic_lines = self.env['account.analytic.line'].browse(active_ids)
            if not account_analytic_lines.filtered(lambda m: not m.is_billed):
                raise ValidationError(_('No Timesheet to make bill.'))
            else:
                for rec in account_analytic_lines.filtered(lambda m: not m.is_billed):
                    vals = {
                        'partner_id': rec.partner_id.id,
                        'name': rec.name,
                        'date': rec.date if rec.date else date.today(),
                        'amount': rec.amount if rec.amount else 0.0,
                        'unit_amount': rec.unit_amount if rec.unit_amount else 0.0,
                        'product_uom_id': rec.product_uom_id.id,
                        'product_id': rec.product_id.id,
                        'account_analytic_line_id': rec.id if rec else False,
                        'project_id': rec.project_id.id if rec.project_id else False,
                        'task_id': rec.task_id.id if rec.task_id else False,
                        'job_cost_id': rec.project_id.job_cost_id.id if rec.project_id.job_cost_id else False,
                    }
                    account_analytic_list.append((0, 0, vals))
                    res.update({
                        'timesheet_bill_wiz_lines': account_analytic_list,
                    })
        return res

    def create_bill_timesheet(self):
        journal = self.env['account.journal'].sudo().search([('type', '=', 'purchase')], limit=1)
        line_vals = []
        for rec in self:
            for line in rec.timesheet_bill_wiz_lines:
                line_val = {
                    'product_id': line.product_id.id if line.product_id else False,
                    'quantity': line.unit_amount if line.unit_amount else 0.0,
                    'price_unit': line.amount if line.amount else 0.0,
                    'name': line.name,
                    'product_uom_id': line.product_uom_id.id if line.product_uom_id else False,
                }
                line_vals.append((0, 0, line_val))

                vals = {
                    'move_type': 'in_invoice',
                    'invoice_date': date.today(),
                    'journal_id': journal.id,
                    'partner_id': line.partner_id.id,
                    'invoice_line_ids': line_vals,
                    'account_analytic_line_id': rec.id,
                    'project_id': line.project_id.id if line.project_id else False,
                    'task_id': line.task_id.id if line.task_id else False,
                    'job_cost_id': line.project_id.job_cost_id.id if line.project_id.job_cost_id else False,                    
                }
                self.env['account.move'].sudo().create(vals)

                if line.account_analytic_line_id:
                    line.account_analytic_line_id.write({'is_billed': True})

class TimesheetBillWizardLine(models.TransientModel):
    _name = 'timesheet.bill.wizard.line'

    name = fields.Char()
    date = fields.Date()
    amount = fields.Float()
    unit_amount = fields.Float()
    partner_id = fields.Many2one('res.partner')
    product_id = fields.Many2one('product.product')
    product_uom_id = fields.Many2one('uom.uom')
    timesheet_bill_wiz_id = fields.Many2one('timesheet.bill.wizard')
    account_analytic_line_id = fields.Many2one('account.analytic.line')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Project Task')

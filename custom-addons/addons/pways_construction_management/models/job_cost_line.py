from odoo import models, fields, api, tools, _

class JobCostLine(models.Model):
    _name = 'job.cost.line'
    _description = 'Job Cost Line'
    _rec_name = 'description'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            rec.product_qty = 1.0
            rec.uom_id = rec.product_id.uom_id.id
            rec.cost_price = rec.product_id.standard_price

    @api.depends('product_qty', 'hours', 'cost_price', 'direct_id')
    def _compute_total_cost(self):
        for rec in self:
            if rec.job_type == 'labour':
                rec.product_qty = 0.0
                rec.total_cost = rec.hours * rec.cost_price
            else:
                rec.hours = 0.0
                rec.total_cost = rec.product_qty * rec.cost_price

    @api.depends('purchase_order_line_ids', 'purchase_order_line_ids.product_qty', 'purchase_order_line_ids.order_id.state')
    def _compute_actual_quantity(self):
        for rec in self:
            rec.actual_quantity = sum(
                [p.product_qty for p in rec.purchase_order_line_ids if p.order_id.state in ['purchase', 'done']]
            )

    @api.depends('timesheet_line_ids', 'timesheet_line_ids.unit_amount')
    def _compute_actual_hour(self):
        for rec in self:
            rec.actual_hour = sum([p.unit_amount for p in rec.timesheet_line_ids])

    @api.depends(
        'account_invoice_line_ids', 'account_invoice_line_ids.quantity', 
        'account_invoice_line_ids.move_id.state', 'account_invoice_line_ids.move_id.payment_state'
    )
    def _compute_actual_invoice_quantity(self):
        for rec in self:
            rec.actual_invoice_quantity = sum(
                [p.quantity for p in rec.account_invoice_line_ids if p.move_id.state in ['posted'] or p.move_id.payment_state in ['paid']]
            )

    direct_id = fields.Many2one('job.costing', string='Job Costing')
    product_id = fields.Many2one('product.product', string='Product', copy=False, required=True)
    description = fields.Char(string='Description', copy=False)
    reference = fields.Char(string='Reference', copy=False)
    date = fields.Date(string='Date', required=True, copy=False)
    product_qty = fields.Float(string='Planned Qty', copy=False)
    uom_id = fields.Many2one('uom.uom', string='Uom')
    cost_price = fields.Float(string='Cost / Unit', copy=False)
    total_cost = fields.Float(string='Cost Price Sub Total', compute='_compute_total_cost', store=True)
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    job_type_id = fields.Many2one('job.type', string='Job Type')
    job_type = fields.Selection(
        selection=[('material', 'Material'), ('labour', 'Labour'), ('overhead', 'Overhead'), ('vehicle','Vehicle'), ('equipment','Equipment'),],
        string="Type",
        required=True
    )
    basis = fields.Char(string='Basis')
    hours = fields.Float(string='Hours')
    purchase_order_line_ids = fields.One2many('purchase.order.line', 'job_cost_line_id')
    timesheet_line_ids = fields.One2many('account.analytic.line', 'job_cost_line_id')
    account_invoice_line_ids = fields.One2many('account.move.line', 'job_cost_line_id')
    actual_quantity = fields.Float(string='Actual Purchased Quantity', compute='_compute_actual_quantity')
    actual_invoice_quantity = fields.Float(string='Actual Vendor Bill Quantity', compute='_compute_actual_invoice_quantity')
    actual_hour = fields.Float(string='Actual Timesheet Hours', compute='_compute_actual_hour')


class JobCostEquipmentFleet(models.Model):
    _name = 'job.cost.equipment.fleet'
    _description = "Job Cost Equipment Fleet"


    @tools.ormcache()
    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_unit')

    request_type = fields.Selection(selection=[('vehicle','Vehicle'),('equipment','Equipment')], string='Type', default='vehicle')
    qty = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    total_price = fields.Float(string="Total Price", compute="_compute_total_cost")
    name = fields.Char(string="Name")
    vehicle_id = fields.Many2one('fleet.vehicle',string='Vehicle')
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    task_id = fields.Many2one('project.task', related="job_costing_id.task_id", string="Task")
    project_id = fields.Many2one('project.project', related="job_costing_id.project_id", string='Project', readonly=False)
    uom_id = fields.Many2one('uom.uom', string='Uom', default=_get_default_uom_id,)
    job_type_id = fields.Many2one('job.type', string='Job Type')
    job_type = fields.Selection(
        selection=[('material', 'Material'), ('labour', 'Labour'), ('overhead', 'Overhead'), ('vehicle','Vehicle'), ('equipment','Equipment'),],
        string="Type",
        required=True
    )
    @api.depends('qty', 'unit_price')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_price = rec.qty * rec.unit_price
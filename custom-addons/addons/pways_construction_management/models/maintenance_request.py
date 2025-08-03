from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    task_id = fields.Many2one('project.task', string='Task')
    project_id = fields.Many2one('project.project', string='Project', readonly=False)
    maintenance_request_line_ids = fields.One2many('maintenance.request.line', 'maintenance_request_id')
    grand_total = fields.Float(string='Grand total', compute="_compute_grand_total")
    picking_count = fields.Integer(compute='_compute_picking_count')
    bill_count = fields.Integer(compute='_compute_bill_count')

    ###### Compute methods ######

    def _compute_picking_count(self):
        picking = self.env['stock.picking']
        for rec in self:
            rec.picking_count = picking.search_count([('maintenance_request_id', '=', self.id)])
        
    def _compute_bill_count(self):
        move = self.env['account.move']
        for rec in self:
            rec.bill_count = move.search_count([('maintenance_request_id', '=', self.id)])

    @api.depends('maintenance_request_line_ids')
    def _compute_grand_total(self):
        total = 0
        for rec in self.maintenance_request_line_ids:
            total += rec.sub_total
        self.grand_total = total

    ###### state button methods ######

    def open_picking_action(self):
        result = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        result['domain'] = str([('maintenance_request_id', '=', self.id)])
        return result

    def open_bills_action(self):
        self.ensure_one()
        bill_action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        bill_action['domain'] = str([('maintenance_request_id', '=', self.id), ('move_type', '=', 'in_invoice')])
        bill_action['context'] = {'default_move_type': 'in_invoice','default_maintenance_request_id':self.id,}
        return bill_action

    ###### Normal button methods ######

    def action_create_bill(self):
        journal = self.env['account.journal'].sudo().search([('type', '=', 'purchase')], limit=1)
        line_vals = []

        for rec in self:
            for maintenance_request_line_id in rec.maintenance_request_line_ids:
                line_val = {
                    'product_id': maintenance_request_line_id.product_id.id,
                    'quantity': maintenance_request_line_id.qty,
                    'price_unit': maintenance_request_line_id.price,
                    'tax_ids': maintenance_request_line_id.tax_ids.ids,
                    'job_cost_id': rec.job_costing_id.id if rec.job_costing_id.id else rec.project_id.job_cost_id.id,
                }
                line_vals.append((0, 0, line_val))

            vals = {
                'move_type': 'in_invoice',
                'invoice_date': date.today(),
                'journal_id': journal.id,
                # 'partner_id': rec.partner_id.id,
                'invoice_line_ids': line_vals,
                'maintenance_request_id': rec.id,
                'project_id': rec.project_id.id if rec.project_id else False,
                'task_id': rec.task_id.id if rec.task_id else False,
                'job_cost_id': rec.job_costing_id.id if rec.job_costing_id.id else rec.project_id.job_cost_id.id,
            }
            self.env['account.move'].sudo().create(vals)


    def action_create_picking(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        for rec in self:
            move_lines = []
            for line in rec.maintenance_request_line_ids:
                move_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.uom_id.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'location_dest_id': warehouse.lot_stock_id.id,
                }))
            picking_vals = {
                'picking_type_id': warehouse.out_type_id.id,
                'location_id': warehouse.lot_stock_id.id,
                'maintenance_request_id': rec.id,
                'move_ids_without_package': move_lines,
                'project_id': rec.project_id.id if rec.project_id else False,
                'task_id': rec.task_id.id if rec.task_id else False,
                'job_cost_id': rec.job_costing_id.id if rec.job_costing_id.id else rec.project_id.job_cost_id.id,
            }
            self.env['stock.picking'].create(picking_vals)

class MaintenanceRequestLine(models.Model):
    _name = 'maintenance.request.line'

    maintenance_request_id = fields.Many2one('maintenance.request')
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    tax_ids = fields.Many2many('account.tax')
    price = fields.Float(string="Price")
    sub_total = fields.Float(string='Sub total', compute="_compute_sub_total")

    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
            rec.price = rec.product_id.lst_price

    @api.depends('price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.qty
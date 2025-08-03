from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class TaskPickingWizard(models.TransientModel):
    _name = 'task.picking.wizard'

    partner_id = fields.Many2one('res.partner')
    picking_type_id = fields.Many2one('stock.picking.type')
    location_id = fields.Many2one('stock.location')
    date = fields.Date()
    task_pick_wiz_lines = fields.One2many('task.picking.wizard.line', 'task_pick_wiz_id')
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Project Task')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account',copy=True,)

    @api.model
    def default_get(self, fields):
        res = super(TaskPickingWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        company_id = self.env.user.company_id
        picking_type_id = self.env.ref('stock.picking_type_out')
        location_id = self.env.ref('stock.stock_location_stock')
        operation_list = []
        product_uom_qty = 0.0
        if active_id:
            task_id = self.env['project.task'].browse(active_id)
            if not task_id.consumed_material_ids.filtered(lambda m: (m.is_picked and m.product_uom_qty > m.consumed_qty) or (not m.is_picked and m.product_uom_qty > m.consumed_qty)):
                raise ValidationError(_('No consumed materials to pick.'))
            else:
                for res_task in task_id:
                    for rec in res_task.consumed_material_ids.filtered(lambda m: (m.is_picked and m.product_uom_qty > m.consumed_qty) or (not m.is_picked and m.product_uom_qty > m.consumed_qty)):
                        product_uom_qty = rec.product_uom_qty - rec.consumed_qty
                        vals = {
                            'product_id': rec.product_id.id,
                            'description': rec.product_id.name,
                            'product_uom_qty': product_uom_qty,
                            'product_uom': rec.product_id.uom_id.id,
                            'is_picked': True,
                            'consumed_material_id': rec.id,
                            'consumed_qty': rec.consumed_qty,
                        }
                        operation_list.append((0, 0, vals))
                    if 'task_pick_wiz_lines' in fields:
                        res.update({
                            'partner_id': res_task.partner_id.id,
                            'task_pick_wiz_lines': operation_list,
                            'date': date.today(),
                            'picking_type_id': picking_type_id.id if picking_type_id else False,
                            'location_id': location_id.id if location_id else False,
                            'task_id': res_task.id if res_task else False,
                            'project_id' : res_task.project_id.id,
                            'job_cost_id' : res_task.job_cost_id.id if res_task.job_cost_id else res_task.project_id.job_cost_id.id,
                        })
                    else:
                        res.update({
                            'partner_id': res_task.partner_id.id,
                            'date': date.today(),
                            'picking_type_id': picking_type_id.id if picking_type_id else False,
                            'location_id': location_id.id if location_id else False,
                            'task_id': res_task.id if res_task else False,
                            'job_cost_id' : res_task.job_cost_id.id if res_task.job_cost_id else res_task.project_id.job_cost_id.id,
                            'project_id' : res_task.project_id.id,
                        })
        return res

    def create_stock_picking(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        for rec in self:
            move_lines = []
            for line in rec.task_pick_wiz_lines:
                move_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': rec.location_id.id if rec.location_id else warehouse.lot_stock_id.id,
                    'location_dest_id': warehouse.lot_stock_id.id,
                }))
            picking_vals = {
                'partner_id': rec.partner_id.id,
                'picking_type_id': rec.picking_type_id.id if rec.picking_type_id else rec.env.ref('stock.picking_type_out').id,
                'task_id': rec.task_id.id,
                'location_id': rec.location_id.id if rec.location_id else warehouse.lot_stock_id.id,
                'move_ids_without_package': move_lines,
                'project_id' : rec.project_id.id,
                'job_cost_id' : rec.job_cost_id.id,
            }
            self.env['stock.picking'].create(picking_vals)
            
            for line in rec.task_pick_wiz_lines:
                consumed_qty = 0.0
                if line.consumed_material_id:
                    consumed_qty = line.product_uom_qty + line.consumed_qty
                    task_vals = {
                            'is_picked': True, 
                            'consumed_qty': consumed_qty,
                    }
                    line.consumed_material_id.write(task_vals)

class TaskPickingWizardLine(models.TransientModel):
    _name = 'task.picking.wizard.line'

    task_pick_wiz_id = fields.Many2one('task.picking.wizard')
    product_id = fields.Many2one('product.product')
    description = fields.Text()
    product_uom_qty = fields.Float()
    product_uom = fields.Many2one('uom.uom')
    consumed_material_id = fields.Many2one('consumed.material')
    is_picked = fields.Boolean()
    consumed_qty = fields.Float()

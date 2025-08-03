from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    custom_requisition_id = fields.Many2one('material.purchase.requisition',string='Requisitions',copy=False)
    picking_id = fields.Many2one('stock.picking',string='Stock Picking')
    task_id = fields.Many2one('project.task', string='Project Task')
    project_id = fields.Many2one('project.project', string='Project')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account',copy=True,)
     
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'project_id': self.project_id.id if self.project_id else False,
            'task_id': self.task_id.id if self.task_id else False,
            'job_cost_id': self.job_cost_id.id if self.job_cost_id else False,
            })
        return invoice_vals

    def _prepare_picking(self):
        picking_vals = super()._prepare_picking()
        picking_vals.update({
            'project_id': self.project_id.id if self.project_id else False,
            'task_id': self.task_id.id if self.task_id else False,
            'job_cost_id': self.job_cost_id.id if self.job_cost_id else False,
            })
        return picking_vals


    #@api.multi THIS METHOD IS NOT USED ANY MORE SINCE THIS FEATURE HAS BEEN REMOVED IN ODOO 13.
    def button_confirm_unused(self):
        result = super(PurchaseOrder,self).button_confirm()
        cost_line_obj = self.env['job.cost.line']
        for order in self:
            for line in order.order_line:
                cost_id = line.job_cost_id
                if not line.job_cost_line_id:
                    if cost_id:
                        hours = 0.0
                        qty = 0.0
                        date = line.date_planned
                        product_id = line.product_id.id
                        description = line.name
                        if line.product_id.type == 'service':
                            job_type = 'labour'
                            hours = line.product_qty
                        else:
                            job_type = 'material'
                            qty = line.product_qty
                            
                        price = line.price_unit
                        vals={
                            'date':date,
                            'product_id':product_id,
                            'description':description,
                            'job_type':job_type,
                            'product_qty':qty,
                            'cost_price':price,
                            'hours':hours,
                        }
                        job_cost_line_id = cost_line_obj.create(vals)
                        line.job_cost_line_id = job_cost_line_id.id
                        job_cost_line_ids = cost_id.job_cost_line_ids.ids
                        job_cost_line_ids.append(job_cost_line_id.id)
                        if job_cost_line_id.job_type == 'labour':
                            cost_vals={
                                'job_labour_line_ids':[(6,0,job_cost_line_ids)],
                        }
                        else:
                            cost_vals={
                                'job_cost_line_ids':[(6,0,job_cost_line_ids)],
                        }
                        cost_id.update(cost_vals)
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    custom_requisition_line_id = fields.Many2one('material.purchase.requisition.line',string='Requisitions Line',copy=False)
    job_cost_id = fields.Many2one('job.costing',string='Job Cost Center')
    job_cost_line_id = fields.Many2one('job.cost.line',string='Job Cost Line')
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account',copy=True,)

    def _prepare_account_move_line(self, move=False):#V14
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        res.update({
            'job_cost_id': self.job_cost_id.id,
            'job_cost_line_id': self.job_cost_line_id.id,
        })
        return res

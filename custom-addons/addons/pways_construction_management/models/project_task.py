from odoo import models, fields, api , _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

class ProjectTask(models.Model):
    _inherit = 'project.task'

    all_bills_count = fields.Integer(compute='_compute_all_bills_count')
    stock_moves_count = fields.Integer(compute='total_stock_moves_count', string='# of Stock Moves',store=True,)
    notes_count = fields.Integer(compute='_compute_notes_count', string="Notes")
    material_reqsn_count = fields.Integer(compute='_compute_material_reqsn_count')
    stock_count = fields.Integer(compute='_compute_stock_count')
    picking_count = fields.Integer(compute='_compute_picking_count')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)
    parent_task_id = fields.Many2one('project.task', string='Project Parent Task', readonly=True)
    process_id = fields.Many2one('construct.process', string='Process')
    move_ids = fields.Many2many('material.purchase.requisition.line',compute='_compute_stock_picking_moves',store=True,)
    job_cost_ids = fields.One2many('job.costing','task_id',)
    picking_ids = fields.One2many('material.purchase.requisition','task_id',string='Stock Pickings')
    material_plan_ids = fields.One2many('material.plan','material_task_id',string='Material Plannings')
    consumed_material_ids = fields.One2many('consumed.material','consumed_task_material_id',string='Consumed Materials')
    child_task_ids = fields.One2many('project.task', 'parent_task_id', string='Child Tasks')
    notes_ids = fields.One2many('note.note', 'task_id', string='Notes Id',)
    job_number = fields.Char(string = "Job Number",copy = False,)
    expense_ids = fields.One2many('hr.expense', 'task_id', string="Expense")
    req_vehcle_line_ids = fields.One2many('vehicle.equipment.request', 'task_id', string='Vehicle', copy=False, domain=[('request_type','=','vehicle')], )
    req_equipment_line_ids = fields.One2many('vehicle.equipment.request', 'task_id', string='Equipment', copy=False, domain=[('request_type','=','equipment')], )
    instruct_qlty_ids = fields.One2many('construct.instruction.qlty.checklist', 'task_id')
    progress_bar = fields.Float(string='Progress Bar', help='Calculate the progress of the task ' 'based on the task stage', compute='_compute_task__progress_bar')
    stage_is_progress = fields.Boolean(related='stage_id.is_progress_stage', help='Status of the task based the ' 'stage')

    ###### Compute methods ######

    @api.depends('stage_id')
    def _compute_task__progress_bar(self):
        for rec in self:
            rec.progress_bar = rec.stage_id.progress_bar

    @api.depends('picking_ids.requisition_line_ids')
    def _compute_stock_picking_moves(self):
        for rec in self:
            rec.ensure_one()
            rec.move_ids = self.env['material.purchase.requisition.line']
            for picking in rec.picking_ids:
                rec.move_ids = picking.requisition_line_ids.ids
 
    def _compute_picking_count(self):
        picking = self.env['stock.picking']
        for task in self:
            task.picking_count = picking.search_count([('task_id', '=', self.id)])
        
    def _compute_all_bills_count(self):
        bill_obj = self.env['account.move']
        for project in self:
            project.all_bills_count = bill_obj.search_count([('task_id.id', '=', self.id)])
            
    def total_stock_moves_count(self):
        for task in self:
            task.stock_moves_count = len(task.move_ids)
    
    def _compute_notes_count(self):
        for task in self:
            task.notes_count = len(task.notes_ids)

    def _compute_material_reqsn_count(self):
        boq = self.env['material.purchase.requisition']
        for project in self:
            project.material_reqsn_count = boq.search_count([('task_id', '=', self.id)])
    
    def _compute_stock_count(self):
        material_plan_ids = self.material_plan_ids.mapped('product_id')
        boq = self.env['product.product']
        self.stock_count = boq.search_count([('id', 'in', material_plan_ids.ids)])

    ###### state button methods ######

    def material_reqsn_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pways_construction_management.action_material_purchase_requisition_job_costing")
        action['domain'] = [('task_id', '=', self.id)]
        return action

    def all_bills_action(self):
        bill_ids = self.env['account.move'].search([('task_id.id', '=', self.id)])
        self.ensure_one()
        bill_action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        bill_action['domain'] = str([('id','in',bill_ids.ids), ('move_type', '=', 'in_invoice')])
        bill_action['context'] = {'default_move_type': 'in_invoice','default_task_id':self.id,'default_analytic_id':self.analytic_account_id.id,}
        return bill_action

    def open_picking_action(self):
        result = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        result['domain'] = str([('task_id', '=', self.id)])
        return result

    def view_stock_moves(self):
        for rec in self:
            stock_move_list = []
            for move in rec.move_ids:
                stock_move_list += move.requisition_id.delivery_picking_id.move_line_ids.ids
        result = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_action")
        result['domain'] = str([('id', 'in', stock_move_list)])
        return result

    def view_notes(self):
        for rec in self:
            res = self.env["ir.actions.actions"]._for_xml_id("pways_construction_management.action_task_note_note")
            res['domain'] = str([('task_id','in',rec.ids)])
        return res

    def stock_view_action(self):
        material_plan_ids = self.material_plan_ids.mapped('product_id')
        self.ensure_one()
        stock_action = self.env['ir.actions.act_window']._for_xml_id('stock.action_product_stock_view')
        stock_action['domain'] = str([('id', 'in', material_plan_ids.ids)])
        return stock_action

    ###### Super methods ######

    @api.model
    def create(self,vals):
        number = self.env['ir.sequence'].next_by_code('project.task')
        vals.update({
            'job_number': number,
        })
        return super(ProjectTask, self).create(vals) 

    ###### Normal button methods ######

    def action_subtask(self):
        res = super(ProjectTask, self).action_subtask()
        res['context'].update({
            'default_parent_task_id': self.id,
        })
        return res

    def btn_out_pick_consume_prod(self):
        vals = {
                'name': 'Picking Wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'task.picking.wizard',
                'target': 'new',
            }
        return vals

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class MaterialPurchaseRequisition(models.Model):
    _name = 'material.purchase.requisition'
    _description = 'Purchase Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'
    
    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel', 'reject'):
                raise UserError(_('You can not delete Purchase Requisition which is not in draft or cancelled or rejected state.'))
        return super(MaterialPurchaseRequisition, self).unlink()
    
    name = fields.Char(string='Number', index=True, readonly=1)
    state = fields.Selection(
        [
            ('draft', 'New'),
            ('dept_confirm', 'Waiting Department Approval'),
            ('ir_approve', 'Waiting IR Approval'),
            ('approve', 'Approved'),
            ('stock', 'Purchase Order Created'),
            ('receive', 'Received'),
            ('cancel', 'Cancelled'),
            ('reject', 'Rejected')
        ],
        default='draft',
        tracking=True
    )
    request_date = fields.Date(string='Requisition Date', default=fields.Date.today(), required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True, copy=True)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
        required=True,
        copy=True
    )
    approve_manager_id = fields.Many2one('hr.employee', string='Department Manager', readonly=True, copy=False)
    reject_manager_id = fields.Many2one('hr.employee', string='Department Manager Reject', readonly=True)
    approve_employee_id = fields.Many2one('hr.employee', string='Approved by', readonly=True, copy=False)
    reject_employee_id = fields.Many2one('hr.employee', string='Rejected by', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, required=True, copy=True)
    location_id = fields.Many2one('stock.location', string='Source Location', copy=True)
    requisition_line_ids = fields.One2many('material.purchase.requisition.line', 'requisition_id', string='Purchase Line', copy=True, domain=[('requisition_type', '=', 'purchase')])
    internal_pick_req_line_ids = fields.One2many('material.purchase.requisition.line', 'requisition_id', string='Internal Line', copy=True, domain=[('requisition_type', '=', 'internal')])
    scrap_req_line_ids = fields.One2many('material.purchase.requisition.line', 'requisition_id', string='Scrap Line', copy=True, domain=[('requisition_type', '=', 'scrap')])
    date_end = fields.Date(string='Deadline', readonly=True, help='Last date for the product to be needed', copy=True)
    date_done = fields.Date(string='Date Done', readonly=True)
    managerapp_date = fields.Date(string='Department Approval Date', readonly=True, copy=False)
    manareject_date = fields.Date(string='Department Manager Reject Date', readonly=True)
    userreject_date = fields.Date(string='Rejected Date', readonly=True, copy=False)
    userrapp_date = fields.Date(string='Approved Date', readonly=True, copy=False)
    receive_date = fields.Date(string='Received Date', readonly=True, copy=False)
    reason = fields.Text(string='Reason for Requisitions', required=False, copy=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True)
    dest_location_id = fields.Many2one('stock.location', string='Destination Location', required=False, copy=True)
    delivery_picking_id = fields.Many2one('stock.picking', string='Internal Picking', readonly=True, copy=False)
    requisiton_responsible_id = fields.Many2one('hr.employee', string='Responsible', copy=True)
    employee_confirm_id = fields.Many2one('hr.employee', string='Confirmed by', readonly=True, copy=False)
    confirm_date = fields.Date(string='Confirmed Date', readonly=True, copy=False)
    purchase_order_ids = fields.One2many('purchase.order', 'custom_requisition_id', string='Purchase Orders')
    custom_picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type', copy=False)
    task_id = fields.Many2one('project.task', string='Task / Job Order')
    task_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Task / Job Order User')
    task_user_ids = fields.Many2many('res.users', related='task_id.user_ids', string='Task / Job Order User')
    project_id = fields.Many2one('project.project', string='Construction Project')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_order_ids = fields.Many2many('purchase.order', string='Purchase Orders')
    equipment_machine_total = fields.Float(compute='compute_equipment_machine', string='Equipment / Machinery Cost', store=True)
    worker_resource_total = fields.Float(compute='compute_equipment_machine', string='Worker / Resource Cost', store=True)
    work_cost_package_total = fields.Float(compute='compute_equipment_machine', string='Work Cost Package', store=True)
    subcontract_total = fields.Float(compute='compute_equipment_machine', string='Subcontract Cost', store=True)
    requisition_type = fields.Selection([('internal', 'Internal Picking'), ('purchase', 'Purchase Order'), ('scrap', 'Scrap Order')], string='Action', default='purchase', required=True )
    scrap_type = fields.Selection([('store', 'Store'), ('scrap', 'Scrap')], string='Scrap Type', default='scrap', required=True )
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center')
        
    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('purchase.requisition.seq')
        vals.update({
            'name': name
            })
        res = super(MaterialPurchaseRequisition, self).create(vals)
        return res
        
    #@api.multi
    def requisition_confirm(self):
        for rec in self:
            manager_mail_template = self.env.ref('pways_construction_management.email_confirm_material_purchase_requistion')
            rec.employee_confirm_id = rec.employee_id.id
            rec.confirm_date = fields.Date.today()
            rec.state = 'dept_confirm'
            if manager_mail_template:
                manager_mail_template.send_mail(self.id)
            
    #@api.multi
    def requisition_reject(self):
        for rec in self:
            rec.state = 'reject'
            rec.reject_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.userreject_date = fields.Date.today()

    #@api.multi
    def manager_approve(self):
        for rec in self:
            rec.managerapp_date = fields.Date.today()
            rec.approve_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            employee_mail_template = self.env.ref('pways_construction_management.email_purchase_requisition_iruser_custom')
            email_iruser_template = self.env.ref('pways_construction_management.email_purchase_requisition')
            employee_mail_template.sudo().send_mail(self.id)
            email_iruser_template.sudo().send_mail(self.id)
            rec.state = 'ir_approve'

    #@api.multi
    def user_approve(self):
        for rec in self:
            rec.userrapp_date = fields.Date.today()
            rec.approve_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'approve'

    #@api.multi
    def reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        pick_vals = {
            'product_id' : line.product_id.id,
            'product_uom_qty' : line.qty,
            'product_uom' : line.uom.id,
            'location_id' : self.location_id.id,
            'location_dest_id' : self.dest_location_id.id,
            'name' : line.product_id.name,
            'picking_type_id' : self.custom_picking_type_id.id,
            'picking_id' : stock_id.id,
            'custom_requisition_line_id' : line.id,
            'company_id' : line.requisition_id.company_id.id,
        }
        return pick_vals

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        po_line_vals = {
                 'product_id': line.product_id.id,
                 'name':line.product_id.name,
                 'product_qty': line.qty,
                 'product_uom': line.uom.id,
                 'date_planned': fields.Date.today(),
                 'price_unit': line.product_id.standard_price,
                 'order_id': purchase_order.id,
                 'analytic_account_id': self.analytic_account_id.id,
                 'custom_requisition_line_id': line.id,
                 'job_cost_id': self.job_cost_id.id if self.job_cost_id else False,
        }
        return po_line_vals
    
    def create_po(self):
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        for rec in self:
            if not rec.requisition_line_ids:
                raise UserError(_('Please create some Purchase lines.'))
            po_dict = {}
            for line in rec.requisition_line_ids:
                if line.requisition_type == 'purchase':
                    if not line.partner_id:
                        raise UserError(_('Please enter atleast one vendor on Purchase Lines for Action Purchase'))
                    for partner in line.partner_id:
                        if partner not in po_dict:
                            po_vals = {
                                'partner_id':partner.id,
                                'currency_id':rec.env.user.company_id.currency_id.id,
                                'date_order':fields.Date.today(),
                                'company_id':rec.company_id.id,
                                'custom_requisition_id':rec.id,
                                'origin': rec.name,
                                'project_id' : rec.project_id.id,
                                'task_id' : rec.task_id.id,
                                'job_cost_id' : rec.job_cost_id.id,
                                'job_cost_id' : rec.job_cost_id.id,
                                'analytic_account_id': self.analytic_account_id.id,
                            }
                            purchase_order = purchase_obj.create(po_vals)
                            po_dict.update({partner:purchase_order})
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
                            purchase_line_obj.sudo().create(po_line_vals)
                        else:
                            purchase_order = po_dict.get(partner)
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
                            purchase_line_obj.sudo().create(po_line_vals)
                rec.state = 'stock'
    
    def create_picking(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        for rec in self:
            if not rec.internal_pick_req_line_ids:
                raise UserError(_('Please create some Internal lines.'))
            if any(line.requisition_type =='internal' for line in rec.internal_pick_req_line_ids):
                if not rec.location_id.id:
                    raise UserError(_('Select Source location under the picking details.'))
                if not rec.custom_picking_type_id.id:
                    raise UserError(_('Select Picking Type under the picking details.'))
                if not rec.dest_location_id:
                    raise UserError(_('Select Destination location under the picking details.'))
                picking_vals = {
                        'partner_id' : rec.employee_id.sudo().address_home_id.id,
                        'location_id' : rec.location_id.id,
                        'location_dest_id' : rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
                        'picking_type_id' : rec.custom_picking_type_id.id,#internal_obj.id,
                        'note' : rec.reason,
                        'custom_requisition_id' : rec.id,
                        'origin' : rec.name,
                        'company_id' : rec.company_id.id,
                        'project_id' : rec.project_id.id,
                        'task_id' : rec.task_id.id,
                        'job_cost_id' : rec.job_cost_id.id,
                    }
                stock_id = stock_obj.sudo().create(picking_vals)
                delivery_vals = {'delivery_picking_id' : stock_id.id,}
                rec.write(delivery_vals)
            po_dict = {}
            for line in rec.internal_pick_req_line_ids:
                if line.requisition_type =='internal':
                    pick_vals = rec._prepare_pick_vals(line, stock_id)
                    move_id = move_obj.sudo().create(pick_vals)
                rec.state = 'stock'

    def create_store_scrap(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        for rec in self:
            if not rec.scrap_req_line_ids:
                raise UserError(_('Please create some Scrap lines.'))
            if not rec.scrap_type:
                raise UserError(_('Select Scrap Type.'))
            if any(line.requisition_type =='scrap' for line in rec.scrap_req_line_ids):
                if not rec.location_id.id:
                    raise UserError(_('Select Source location under the picking details.'))
                if not rec.custom_picking_type_id.id:
                    raise UserError(_('Select Picking Type under the picking details.'))
                if not rec.dest_location_id:
                    raise UserError(_('Select Destination location under the picking details.'))
                picking_vals = {
                        'partner_id' : rec.employee_id.sudo().address_home_id.id,
                        'location_id' : rec.location_id.id,
                        'location_dest_id' : rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
                        'picking_type_id' : rec.custom_picking_type_id.id,
                        'note' : rec.reason,
                        'custom_requisition_id' : rec.id,
                        'origin' : rec.name,
                        'company_id' : rec.company_id.id,
                        'project_id' : rec.project_id.id,
                        'task_id' : rec.task_id.id,
                        'job_cost_id' : rec.job_cost_id.id,
                    }
                stock_id = stock_obj.sudo().create(picking_vals)
                delivery_vals = {'delivery_picking_id' : stock_id.id,}
                rec.write(delivery_vals)
            po_dict = {}
            for line in rec.scrap_req_line_ids:
                if line.requisition_type =='scrap':
                    pick_vals = rec._prepare_pick_vals(line, stock_id)
                    move_id = move_obj.sudo().create(pick_vals)
                rec.state = 'stock'

    #@api.multi
    def action_received(self):
        for rec in self:
            rec.receive_date = fields.Date.today()
            rec.state = 'receive'
    
    #@api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def show_picking(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('stock.action_picking_tree_all')
        res['domain'] = str([('custom_requisition_id','=',self.id)])
        return res

    def show_scrap_store_picking(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('stock.action_picking_tree_all')
        res['domain'] = str([('custom_requisition_id','=',self.id)])
        return res
        
    #@api.multi
    def action_show_po(self):
        self.ensure_one()
        purchase_action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        purchase_action['domain'] = str([('custom_requisition_id','=',self.id)])
        return purchase_action

    ###### Onchange methods ######
    
    @api.onchange('employee_id')
    def set_department(self):
        for rec in self:
            rec.department_id = rec.employee_id.sudo().department_id.id
            rec.dest_location_id = rec.employee_id.sudo().dest_location_id.id or rec.employee_id.sudo().department_id.dest_location_id.id 

    @api.onchange('requisition_type', 'scrap_type')
    def onchange_scrap_type(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        scrap_location = self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)  # Corrected line

        for rec in self:
            if rec.requisition_type == 'scrap':
                if rec.scrap_type == 'scrap':
                    rec.location_id = warehouse.lot_stock_id.id if warehouse else False
                    rec.dest_location_id = scrap_location if scrap_location else False
                    rec.custom_picking_type_id = warehouse.out_type_id.id if warehouse else False
                if rec.scrap_type == 'store':
                    rec.location_id = scrap_location if scrap_location else False
                    rec.dest_location_id = warehouse.lot_stock_id.id if warehouse else False
                    rec.custom_picking_type_id = warehouse.int_type_id.id if warehouse else False
            if rec.requisition_type == 'internal':
                if rec.employee_id:
                    rec.department_id = rec.employee_id.sudo().department_id.id
                    rec.dest_location_id = rec.employee_id.sudo().dest_location_id.id or rec.employee_id.sudo().department_id.dest_location_id.id 
    
    @api.onchange('task_id')
    def onchange_project_task(self):
        plan_materials = []
        for rec in self:
            # rec.project_id = rec.task_id.project_id.id
            # rec.task_user_id = rec.task_id.user_ids[0].id if rec.task_id.user_ids else False
            rec.analytic_account_id = rec.task_id.project_id.analytic_account_id.id
            if rec.task_id:
                rec.requisition_line_ids = [(5, 0, 0)]
                if rec.task_id.material_plan_ids:
                    for plan in rec.task_id.material_plan_ids:
                        plan_materials.append((0, 0, {
                            'product_id': plan.product_id.id,
                            'description': plan.description,
                            'qty': 0.0,
                            'uom': plan.product_id.uom_id.id,
                        }))
                    rec.requisition_line_ids = plan_materials

    ###### Compute methods ######

    #@api.multi
    @api.depends('requisition_line_ids',
                 'requisition_line_ids.product_id',
                 'requisition_line_ids.product_id.boq_type')
    def compute_equipment_machine(self):
        eqp_machine_total = 0.0
        work_resource_total = 0.0
        work_cost_package_total = 0.0
        subcontract_total = 0.0
        for rec in self:
            for line in rec.requisition_line_ids:
                if line.product_id.boq_type == 'eqp_machine':
                    eqp_machine_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'worker_resource':
                    work_resource_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'work_cost_package':
                    work_cost_package_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'subcontract':
                    subcontract_total += line.product_id.standard_price * line.qty
            rec.equipment_machine_total = eqp_machine_total
            rec.worker_resource_total = work_resource_total
            rec.work_cost_package_total = work_cost_package_total
            rec.subcontract_total = subcontract_total


class MaterialPurchaseRequisitionLine(models.Model):
    _name = "material.purchase.requisition.line"
    _description = 'Material Purchase Requisition Lines'

    requisition_id = fields.Many2one('material.purchase.requisition', string='Requisitions')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    # layout_category_id = fields.Many2one('sale.layout_category', string='Section')
    description = fields.Char(string='Description', required=True)
    qty = fields.Float(string='Quantity', default=1, required=True)
    uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    partner_id = fields.Many2many('res.partner', string='Vendors')
    requisition_type = fields.Selection(selection=[('internal', 'Internal Picking'), ('purchase', 'Purchase Order'), ('scrap', 'Scrap Order')],
        string='Requisition Action', default='purchase', required=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            rec.uom = rec.product_id.uom_id.id


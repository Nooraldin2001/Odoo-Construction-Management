from odoo import models, fields, api , _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class ProjectProject(models.Model):
    _inherit = "project.project" 

    @api.model
    def default_get_warehouse(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        return warehouse.id if warehouse else False

    longitude = fields.Char(string='Longitude')
    latitude = fields.Char(string='Latitude')
    phone = fields.Char(related="partner_id.phone")
    mobile = fields.Char(related="partner_id.mobile")
    email = fields.Char(related="partner_id.email")
    site_name = fields.Char()
    site_length = fields.Float()
    site_width = fields.Float()
    site_area = fields.Float()
    progressbar = fields.Float(string='Progress Bar', compute='_compute_progress_bar', help='Calculate the progress of the task ' 'based on the task stage')
    is_progress_bar = fields.Boolean(string='Is Progress Bar', help='Status of the task based the ' 'stage')
    type_of_construction = fields.Selection(
        [('agricultural','Agricultural'),
        ('residential','Residential'),
        ('commercial','Commercial'),
        ('institutional','Institutional'),
        ('industrial','Industrial'),
        ('heavy_civil','Heavy civil'),
        ('environmental','Environmental'),
        ('other','other')],
        string='Types of Construction'
    )
    state = fields.Selection(
        [('draft','Draft'),
        ('confirm','Confirmed'),
        ('in_approve','Internal Approved'),
        ('govt_approve','Govt. Approved'),
        ('in_progress','In Progress'),
        ('ready_to_possession','Ready To Possession'),
        ('read_to_move','Ready To Move'),
        ('cancel','Canceled')],
        default="draft",
    )
    warehouse_id = fields.Many2one('stock.warehouse', default=default_get_warehouse)
    construct_cycle_id = fields.Many2one('construct.cycle', string='Cycles')
    location_id = fields.Many2one('res.partner',string='Location')
    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center',)
    notes_count = fields.Integer(compute='_compute_notes_count', string="Notes",)
    job_cost_count = fields.Integer(compute='_compute_jobcost_count')
    material_reqsn_count = fields.Integer(compute='_compute_material_reqsn_count')
    po_count = fields.Integer(compute='_compute_mrq_po_count')
    maintenance_req_count = fields.Integer(compute='_compute_maintenance_req_count')
    all_bills_count = fields.Integer(compute='_compute_all_bills_count')
    in_picking_count = fields.Integer(compute='_compute_in_picking_count')
    notes_ids = fields.One2many('note.note', 'project_id', string='Notes Id',)
    job_cost_ids = fields.One2many('job.costing','project_id',)
    expense_ids = fields.One2many('hr.expense', 'project_id', string="Expense")
    construction_daily_logs_ids = fields.One2many('construct.daily.logs', 'project_id', string="Construction Daily Logs")
    project_construct_line_ids = fields.One2many('project.construct.line', 'project_id')
    document_ids = fields.Many2many('ir.attachment', string="Documents")
    stack_holder_ids = fields.Many2many('res.users')
    process_ids = fields.Many2many('construct.process', string="Process")

    @api.model
    def create(self, vals):
        rtn = super(ProjectProject, self).create(vals)
        stage_obj = self.env['project.task.type']
        stage_ids = stage_obj.search([('set_default', '=', True)])
        project_ids = [x.id for x in rtn]
        for stage in stage_ids:
            stage.sudo().write({'project_ids': [(4, tuple(project_ids), 0)]})
        return rtn

    ###### Compute methods ######
    
    @api.depends('task_ids')
    def _compute_progress_bar(self):
        for rec in self:
            progressbar_tasks = self.env['project.task'].search([('project_id', '=', rec.id)]).filtered(
                lambda progress: progress.stage_id.is_progress_stage == True)
            if progressbar_tasks:
                rec.progressbar = (sum(progressbar_tasks.mapped(
                    'progress_bar'))) / len(progressbar_tasks)
            else:
                rec.progressbar = 0

    @api.depends()
    def _compute_notes_count(self):
        self.notes_count = len(self.notes_ids)

    #@api.multi
    def _compute_jobcost_count(self):
        job_cost_ids = self.mapped('job_cost_ids')
        self.job_cost_count = self.env['job.costing'].search_count([('id', 'in', job_cost_ids.ids)])

    def _compute_material_reqsn_count(self):
        self.material_reqsn_count = self.env['material.purchase.requisition'].search_count([('project_id', '=', self.id)])

    def _compute_mrq_po_count(self):
        mrq_ids = self.env['material.purchase.requisition'].search([('project_id', '=', self.id)])
        self.po_count = self.env['purchase.order'].search_count([('custom_requisition_id','in',mrq_ids.ids)])
    
    def _compute_all_bills_count(self):
        self.all_bills_count = self.env['account.move'].search_count([('project_id', '=', self.id), ])

    def _compute_maintenance_req_count(self):
        self.maintenance_req_count = self.env['maintenance.request'].search_count([('project_id.id', '=', self.id)])

    def _compute_in_picking_count(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        self.in_picking_count = self.env['stock.picking'].search_count([('project_id', '=', self.id), ('picking_type_id', '=', warehouse.in_type_id.id)])
        
    ###### state button methods ######

    def open_in_picking_action(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        result = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        result['domain'] = str([('project_id', '=', self.id), ('picking_type_id', '=', warehouse.in_type_id.id)])
        return result

    def view_notes(self):
        res = self.env["ir.actions.actions"]._for_xml_id("pways_construction_management.action_project_note_note")
        res['domain'] = str([('project_id','in',self.ids)])
        return res

    def project_to_jobcost_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pways_construction_management.action_job_costing")
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id':self.id,'default_analytic_id':self.analytic_account_id.id,'default_user_id':self.user_id.id}
        return action

    def material_reqsn_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pways_construction_management.action_material_purchase_requisition_job_costing")
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def mrq_po_action(self):
        mrq_ids = self.env['material.purchase.requisition'].search([('project_id', '=', self.id)])
        self.ensure_one()
        purchase_action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        purchase_action['domain'] = str([('custom_requisition_id','in',mrq_ids.ids)])
        return purchase_action

    def all_bills_action(self):
        all_bills = self.env['account.move'].search([('project_id', '=', self.id), ])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bills',
            'res_model': 'account.move',
            'domain': [('id', 'in', all_bills.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def maintenance_req_action(self):
        maintenance_req_action = self.env['ir.actions.act_window']._for_xml_id('maintenance.hr_equipment_request_action')
        maintenance_req_action['domain'] = str([('project_id.id', '=', self.id)])
        return maintenance_req_action

    ###### Normal button methods ######

    def action_draft(self):
        self.state = 'draft'
        return True

    def action_confirm(self):
        self.state = 'confirm'
        return True

    def action_in_approve(self):
        self.state = 'in_approve'
        return True
        
    def action_govt_approve(self):
        self.state = 'govt_approve'
        return True
        
    def action_in_progress(self):
        self.state = 'in_progress'
        return True
        
    def action_ready_to_possession(self):
        self.state = 'ready_to_possession'
        return True
        
    def action_read_to_move(self):
        self.state = 'read_to_move'
        return True

    def action_cancel(self):
        self.state = 'cancel'
        return True

    def action_construct_in_picking(self):
        company = self.env.company
        move_id = self.env['stock.move']
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        lot_stock_id = warehouse_id.lot_stock_id
        vendor_location_id = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)

        for rec in self:
            detail_lines = []
            res = []
            move_line_ids = []
            move_vals_ids = []
            for line in rec.project_construct_line_ids:
                if line.product_id.tracking == 'serial':
                    for i in range(0, int(line.qty)):
                        res.append({
                            'qty_done': 1,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.uom_id.id,
                            'location_id': vendor_location_id.id,
                            'location_dest_id': lot_stock_id.id,
                            'lot_id': False,
                            'lot_name': False,
                        })

                    move_line_ids = [(0, 0, move_line) for move_line in res]
                    
                    move_vals = {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.uom_id.id,
                        'location_id': vendor_location_id.id,
                        'location_dest_id': lot_stock_id.id,
                        'product_uom_qty': line.qty,
                        'move_line_ids': move_line_ids,
                    }
                    move_vals_ids.append((0, 0, move_vals))
                    
        picking_vals = {
            'picking_type_id': warehouse_id.in_type_id.id,
            'location_id': vendor_location_id.id,
            'project_id': rec.id,
            'partner_id': rec.partner_id.id,
            'move_ids_without_package': move_vals_ids,
            'job_cost_id': rec.job_cost_id.id,
        }
        picking_id = self.env['stock.picking'].create(picking_vals)
        if picking_id.state == 'draft':
            picking_id.action_confirm()
            for move in picking_id.move_ids_without_package:
                if move.move_line_nosuggest_ids or move.move_line_ids:
                    move.action_clear_lines_show_details()
                    move.action_assign_serial_show_details()
        return True

    def action_create_tasks(self):
        task = self.env['project.task']
        for act in self:
            for block in act.construct_cycle_id:
                for process in block.process_ids:
                    existing_task = task.search([('process_id', '=', process.id), ('project_id', '=', act.id)], limit=1)
                    if existing_task:
                        continue
                    planned_hours = process.hours
                    title = "%s-%s-%s" %(act.name, process.name, act.partner_id.name)
                    description = process.description
                    values = {
                        'name': title,
                        'planned_hours': planned_hours,
                        'partner_id': act.partner_id.id,
                        'email_from': act.partner_id.email,
                        'description': description,
                        'project_id': act.id,
                        'company_id': act.company_id.id,
                        'user_ids': False,
                        'process_id': process.id,
                        'job_cost_id' : act.job_cost_id.id,
                        'analytic_account_id': act.analytic_account_id.id,
                    }
                    task = self.env['project.task'].sudo().create(values)

    def action_expense_xls_rprt(self):
        active_id = self._context.get('active_id')
        active_ids = self._context.get('active_ids')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/project/expense_xls_report/%s' % (active_id),
            'target': 'new',
        }

    def action_send_by_mail(self):
        self.ensure_one()
        template_id = self.env.ref('pways_construction_management.email_template_send_project_details')
        attachments = []
        for image in self.image_ids:
            attachments.append((image.name, image.datas))

        ctx = {
            'default_model': 'project.project',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id if template_id else None,
            'default_composition_mode': 'comment',
            'force_email': True,
            'email_to': self.partner_id.email,
            'default_attachment_ids': [(6, 0, [attachment.id for attachment in self.image_ids])],
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


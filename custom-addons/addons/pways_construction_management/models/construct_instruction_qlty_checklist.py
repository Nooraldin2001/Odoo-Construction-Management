from odoo import api, fields, models, _
from datetime import datetime, date

class ConstructInstructionQltyChecklist(models.Model):
    _name = 'construct.instruction.qlty.checklist'
    _description = "Construction Instruction and Quality Checklist"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    card_instruction_type = fields.Selection(selection=[('instruction','Instruction'), ('qlty_checklist','Quality Checklist')], string='Type', default='instruction')
    task_id = fields.Many2one('project.task', string="Task")

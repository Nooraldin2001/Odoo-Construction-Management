from odoo import models, fields
import random

class ConstructComplianceTags(models.Model):
    _name = 'construct.compliance.tags'
    _description = 'Construct compliance Tags'

    def get_default_color(self):
        color = random.randint(1, 10)
        return color

    name = fields.Char(string='Name')
    color = fields.Integer(default=get_default_color)


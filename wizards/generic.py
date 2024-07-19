from odoo import api, fields, models, _
from odoo.exceptions import UserError

class BSGenericWizard(models.TransientModel):
    _name = 'bs.gen.wizard'
    _description = 'BS Generic Wizard'

    reason = fields.Selection([('1','test1'),
                             ('2','test2'),
                             ('3','test3')], string="Reason")
    more_info = fields.Text('More Information')


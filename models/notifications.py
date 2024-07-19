from odoo import api, fields, models, _
import datetime
from datetime import datetime

class BSNotifications(models.Model):
    _name = 'bs.notification'

    name = fields.Char('Ref#')
    partner_id = fields.Many2one('res.partner', 'Partner')
    content = fields.Text('Notification Content')
    url = fields.Char('Redirecting URL')
    type = fields.Selection([('generic', 'Generic'),
                             ('product', 'Product'),
                             ('order','Order')], string='Notification Type',help="For frontend image control")
    read = fields.Boolean('Was Read?', default=False)
    read_time = fields.Datetime('Notification Read Time')

    @api.model
    def create(self, vals):
        Notification = super(BSNotifications, self).create(vals)
        Notification.name = self.env['ir.sequence'].next_by_code('bs.notification.code')
        return Notification

    def write(self, vals):
        res = super(BSNotifications, self).write(vals)
        if not self.name: self.env['ir.sequence'].next_by_code('bs.notification.code')
        return res


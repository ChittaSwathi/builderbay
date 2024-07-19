from odoo import api, fields, models, _
from odoo.http import request

class BSSmsLog(models.Model):
    _name = "bs.sms.log"
    _order = "id desc"

    name = fields.Char('SMS Record Name')
    res_id = fields.Char('Related Document ID')
    model = fields.Char('Related Document Model')
    sms_type = fields.Selection([('otp', 'OTP'),
                                 ('trans', 'Transactional')], string='Type')
    subtype = fields.Selection([('signin', 'Sign-In OTP'),
                                ('signup','Sign-Up OTP'),
                                ('reset_pass', 'Reset Password OTP'),
                                ('others', 'Others')], string='Subtype')
    body = fields.Text('SMS')
    sent_time = fields.Datetime('SMS Sent At')
    partner_id = fields.Many2one('res.partner', string='Customer')
    recipient_id = fields.Many2one('res.partner', string='Receipient')
    mobile = fields.Char('Mobile')
    email = fields.Char(string='Email')
    # gateway_id = fields.Many2one('gateway_setup', string='Gateway')
    response = fields.Char('Response')
    otp = fields.Char('OTP')



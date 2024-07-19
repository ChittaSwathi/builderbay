from odoo import _, api, fields, models

class BSResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    outgng_sms = fields.Boolean('Outgoing SMS')
    outgng_mail = fields.Boolean('Outgoing Mails')
    otp_expiry_time = fields.Integer('OTP Expiry In', default=120)
    outgng_sms_vendor = fields.Boolean('Outgoing SMS')
    outgng_mail_vendor = fields.Boolean('Outgoing Mails')
    outgng_sms_sp = fields.Boolean('Outgoing SMS')
    outgng_mail_sp = fields.Boolean('Outgoing Mails')
    outgng_sms_dp = fields.Boolean('Outgoing SMS')
    outgng_mail_dp = fields.Boolean('Outgoing Mails')
    outgng_sms_inusr = fields.Boolean('Outgoing SMS')
    outgng_mail_inusr = fields.Boolean('Outgoing Mails')

    notify_rfq_emails = fields.Char('Email Notify RFQ Creation')
    notify_rfq_sms = fields.Char('SMS Notify RFQ Creation')

    def set_values(self):
        super(BSResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("bs.outgng_sms", self.outgng_sms or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_mail", self.outgng_mail or False)
        self.env['ir.config_parameter'].set_param("bs.otp_expiry_time", self.otp_expiry_time or 120)
        self.env['ir.config_parameter'].set_param("bs.notify_rfq_emails", self.notify_rfq_emails or '')
        self.env['ir.config_parameter'].set_param("bs.notify_rfq_sms", self.notify_rfq_sms or '')
        
        self.env['ir.config_parameter'].set_param("bs.outgng_sms_vendor", self.outgng_sms_vendor or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_mail_vendor", self.outgng_mail_vendor or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_sms_sp", self.outgng_sms_sp or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_mail_sp", self.outgng_mail_sp or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_sms_dp", self.outgng_sms_dp or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_mail_dp", self.outgng_mail_dp or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_sms_inusr", self.outgng_sms_inusr or False)
        self.env['ir.config_parameter'].set_param("bs.outgng_mail_inusr", self.outgng_mail_inusr or False)

    def get_values(self):
        res = super(BSResConfigSettings, self).get_values()
        outgng_sms = self.env['ir.config_parameter'].sudo().get_param('bs.outgng_sms', False)
        outgng_mail = self.env['ir.config_parameter'].sudo().get_param('bs.outgng_mail', False)
        otp_expiry_time = self.env['ir.config_parameter'].sudo().get_param('bs.otp_expiry_time', 120)
        notify_rfq_emails = self.env['ir.config_parameter'].sudo().get_param('bs.notify_rfq_emails', 'all@builderbay.com')
        notify_rfq_sms = self.env['ir.config_parameter'].sudo().get_param('bs.notify_rfq_sms', '9642496424')
        outgng_sms_vendor = self.env['ir.config_parameter'].sudo().get_param("bs.outgng_sms_vendor", False)
        outgng_mail_vendor = self.env['ir.config_parameter'].sudo().get_param("bs.outgng_mail_vendor", False)
        outgng_sms_sp = self.env['ir.config_parameter'].sudo().get_param("bs.outgng_sms_sp", False)
        outgng_mail_sp = self.env['ir.config_parameter'].sudo().get_param("bs.outgng_mail_sp", False)
        outgng_sms_dp= self.env['ir.config_parameter'].sudo().get_param("bs.outgng_sms_dp", False)
        outgng_mail_dp = self.env['ir.config_parameter'].sudo().get_param("bs.outgng_mail_dp", False)
        outgng_sms_inusr = self.env['ir.config_parameter'].sudo().get_param("bs.outgng_sms_inusr", False)
        outgng_mail_inusr = self.env['ir.config_parameter'].sudo().get_param("bs.outgng_mail_inusr", False)
        res.update(outgng_sms = bool(outgng_sms),
                    outgng_mail = bool(outgng_mail),
                    otp_expiry_time = int(otp_expiry_time),
                    notify_rfq_emails = notify_rfq_emails,
                    notify_rfq_sms = notify_rfq_sms,
                    outgng_sms_vendor = bool(outgng_sms_vendor),
                    outgng_mail_vendor = bool(outgng_mail_vendor),
                    outgng_sms_sp = bool(outgng_sms_sp),
                    outgng_mail_sp = bool(outgng_mail_sp),
                    outgng_sms_dp = bool(outgng_sms_dp),
                    outgng_mail_dp = bool(outgng_mail_dp),
                    outgng_sms_inusr = bool(outgng_sms_inusr),
                    outgng_mail_inusr = bool(outgng_mail_inusr)
                    )
        return res
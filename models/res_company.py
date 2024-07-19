from odoo import api, fields, models, _
import datetime
from datetime import datetime
import requests

class BSResCompany(models.Model):
    _inherit = 'res.company'
    #
    # footer_link_ids = fields.One2many('bs.footer.links', 'company_id', string='Footer Links')
    # header_search_ids = fields.One2many('bs.header.search', 'company_id', string="Header Search")

    #GST API
    gst_url = fields.Char('GST URL', help="URL that API hits to for response, storing it for change from their end")
    gst_agent_key = fields.Char('Agent Key', help="Agent key will be available in GST portal dashboard.")
    gst_pre_prod_key = fields.Char('Pre Production Key', help="Generate pre-production key under GST portal. This will be only for test purpose.")
    gst_prod_key = fields.Char('Production Key', help="Generate production key under GST portal.")

    # Customer Care / Service
    cust_care_phone = fields.Char('Phone', help="Customer Care number that customers can reach to.")
    cust_care_email = fields.Char('Email', help="Customer Care email that customers can email to.")

    corporate_code = fields.Char('Corporate Code')
    # NEFT/RTGS
    bank_id = fields.Many2one('res.bank', 'Bank')
    ifsc_code = fields.Char('IFSC Code')
    bank_address = fields.Char('Bank Address')

    #SMS OTP
    sms_username = fields.Char('Username')
    sms_password = fields.Char('Password')
    sms_senderid = fields.Char('Sender ID', help="Should be whitelisted.")
    sms_apikey = fields.Char('API Key')
    sms_template_ids = fields.One2many('bs.sms.template', 'company_id', 'SMS Templates')

    old_address_ids = fields.One2many('bs.old.address','company_id','Old Address')

    def get_sms_token(self):
        if not self: self = self.browse(1)
        if self.sms_username and self.sms_password:
            response = requests.post('https://cts.myvi.in:8443/ManageSms/api/AuthJwt/Authenticate',
                                 data={'username': self.sms_username, 'password':self.sms_password})
            if response: return response.json()
        return ""


class BSFooterLinks(models.Model):
    _name = 'bs.footer.links'
    _description = 'Footer Links'

    name = fields.Char('Label')
    page_url = fields.Char('Redirecting URL')
    link_ids = fields.One2many('bs.footer.sublinks','footer_link_id','Links')
    footer_link_id = fields.Many2one('bs.homepage')

class BSFooterSubLinks(models.Model):
    _name = 'bs.footer.sublinks'
    _description = 'Footer Sublinks'
    _order = "sequence"

    name = fields.Char('Name')
    page_url = fields.Char('Redirecting URL')
    sequence = fields.Integer('Sequence', help="Sequence used to order Links for Footer")
    footer_link_id = fields.Many2one('bs.footer.links')


class BSBannerImages(models.Model):
    _name = 'banner.image'
    _description = 'Banner Images'
    _inherit = 'image.mixin'

    name = fields.Char(string='Description', help="Description of banner.")
    color = fields.Char(string='Hex Color Code', help='Homepage Background Color')
    redirecting_url = fields.Char('Redirecting URL', help="URL to redirect to")
    # ecomm_categ_id = fields.Many2one('product.public.category', string='Category', help="Set Category to redirect to onclicking a banner.")
    banner_id = fields.Many2one('bs.homepage')
    ecomm_id = fields.Many2one('product.public.category')
    banner_content = fields.Html('Banner Content')
    s3_url = fields.Char('S3 Bucket URL', help="To get image from s3 bucket")

class BSSMSTemplates(models.Model):
    _name = "bs.sms.template"
    _description = 'SMS Template'

    name = fields.Char('Template Name')
    content = fields.Text('Content')
    company_id = fields.Many2one('res.company')

class BSOldAddress(models.Model):
    _name = "bs.old.address"

    name = fields.Char('Short Name')
    address = fields.Html('Address')
    date_from = fields.Date('From')
    date_to = fields.Date('To')
    company_id = fields.Many2one('res.company')
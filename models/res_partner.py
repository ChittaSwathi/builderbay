from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import datetime
from odoo.http import request
import pyotp
from ast import literal_eval
from odoo.addons.website.models import ir_http
import requests
import re
from odoo.osv.expression import get_unaccent_wrapper

class BSResPartner(models.Model):
    _inherit = "res.partner"

    district_id = fields.Many2one("bs.district", string='District')
    customer_type = fields.Selection([('b2b', 'B2B'),
                                      ('b2c', 'B2C'),], string='Customer Type')
    gst_ids = fields.One2many('bs.gst','partner_id','GSTs')
    is_default_addr = fields.Boolean(help='to set default bill or ship address', default=False)
    site_name = fields.Char('Site Name')
    site_location = fields.Char('Site Location')
    landmark = fields.Char('Landmark')
    default_shipping_id = fields.Many2one('res.partner') #For website
    legal_name = fields.Char(string="Legal Name")
    trade_name  = fields.Char("Trade Name")

    # Customer Specific account details
    partner_code = fields.Char('Partner Code', copy=False, tracking=True)
    bs_acct_no = fields.Char('Bank Account No.', help="Customer specific bank account no. as per builderbay.",
                             copy=False, tracking=True)
    bs_acct_bank_id = fields.Many2one('res.bank','Bank')
    bs_acct_ifsc_code = fields.Char('IFSC Code')
    bs_acct_beneficiary_name = fields.Char('Beneficiary Name', copy=False, tracking=True)
    bs_acct_address = fields.Char('Bank Address')

    to_notify_sms = fields.Boolean('Notify SMS', default=True, tracking=True, copy=False)
    to_notify_email = fields.Boolean('Notify Email', default=True, tracking=True, copy=False)

    _sql_constraints = [
        ('bank_code_uniq', 'unique (bs_acct_no)',"A bank account number with this sequence already exists."),
        ('partner_code_uniq', 'unique (partner_code)', "A partner code with this sequence already exists."),
    ]
    def _compute_last_website_so_id(self):
        SaleOrder = self.env['sale.order']
        for partner in self:
            is_public = any(u._is_public() for u in partner.with_context(active_test=False).user_ids)
            website = ir_http.get_request_website()
            if website and not is_public:
                partner.last_website_so_id = SaleOrder.search([
                    ('partner_id', '=', partner.id),
                    ('website_id', '=', website.id),
                    ('state', '=', 'sent'),
                ], order='write_date desc', limit=1)
            else:
                partner.last_website_so_id = SaleOrder  # Not in a website context or public User

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        self = self.with_user(name_get_uid or self.env.uid)
        # as the implementation is in SQL, we force the recompute of fields if necessary
        self.recompute(['display_name'])
        self.flush()
        if args is None:
            args = []
        order_by_rank = self.env.context.get('res_partner_search_mode')
        if (name or order_by_rank) and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            from_str = from_clause if from_clause else 'res_partner'
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            fields = self._get_name_search_order_by_fields()

            query = """SELECT res_partner.id
                             FROM {from_str}
                          {where} ({email} {operator} {percent}
                               OR {display_name} {operator} {percent}
                               OR {reference} {operator} {percent}
                               OR {vat} {operator} {percent}
                               OR {bs_acct_no} {operator} {percent})
                               -- don't panic, trust postgres bitmap
                         ORDER BY {fields} {display_name} {operator} {percent} desc,
                                  {display_name}
                        """.format(from_str=from_str,
                                   fields=fields,
                                   where=where_str,
                                   operator=operator,
                                   email=unaccent('res_partner.email'),
                                   display_name=unaccent('res_partner.display_name'),
                                   reference=unaccent('res_partner.ref'),
                                   percent=unaccent('%s'),
                                   vat=unaccent('res_partner.vat'),
                                   bs_acct_no = unaccent('res_partner.bs_acct_no'))

            where_clause_params += [search_name] * 3  # for email / display_name, reference
            where_clause_params += [re.sub('[^a-zA-Z0-9]+', '', search_name) or None]  # for vat
            where_clause_params += [search_name]  # for bs_acct_no
            where_clause_params += [search_name]  # for order by
            print(query, where_clause_params)
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            return [row[0] for row in self.env.cr.fetchall()]

        return super(BSResPartner, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''
        if partner.bs_acct_no: name = '[' + str(partner.bs_acct_no) + ']' + str(name)

        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                name = self._get_contact_name(partner, name)
        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = name.replace('\n\n', '\n')
        name = name.replace('\n\n', '\n')
        if self._context.get('address_inline'):
            name = name.replace('\n', ', ')
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        return name

    @api.model
    def create(self, vals):
        partner = super(BSResPartner, self).create(vals)
        if not partner.parent_id and not partner.partner_code :
            if partner.supplier_rank > partner.customer_rank:
                partner.partner_code = self.env['ir.sequence'].next_by_code('bs.vendor.code')
            else:
                if partner.customer_type == 'b2c':
                    partner.partner_code = self.env['ir.sequence'].next_by_code('bs.b2c.code')
                else:
                    if partner.company_type == 'company' and partner.vat:
                        partner.partner_code = self.env['ir.sequence'].next_by_code('bs.partner.code')
        if (partner.partner_code) and not partner.bs_acct_no and self.env.company.corporate_code: #partner.company_type == 'company' and partner.vat --removed
            partner.bs_acct_no = self.env.company.corporate_code + partner.partner_code
            partner.bs_acct_bank_id = self.env.company.bank_id.id
            partner.bs_acct_ifsc_code = self.env.company.ifsc_code
            partner.bs_acct_address = self.env.company.bank_address
            partner.bs_acct_beneficiary_name = partner.name
        return partner

    def write(self, vals):
        res = super(BSResPartner, self).write(vals)
        for rec in self:
            if not rec.parent_id and not self.bs_acct_no: rec.generate_ban_code() # Generates Partner & BS account code
        return res


    def _display_address(self, without_company=False):
        address_format = self._get_address_format()
        args = {
            'bs_acct_no': self.bs_acct_no or self.partner_code or '',
            'state_code': self.state_id.l10n_in_tin or '',
            'state_name':  self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
        }
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '\033[1m' + '%(company_name)s\n' + '\033[1m' + address_format
        return address_format % args

    @api.model
    def update_address(self, vals):
        if vals.get('addr_id', False):
            pid = int(vals.get('addr_id'))
            del vals['addr_id']
            partner = self.browse(pid)
            partner.write(vals)
        return True

    @api.model
    def removeAddr(self, vals):
        try:
            partner = self.browse(int(vals.get('addr_id')))
            if partner:
                partner.unlink()
                return True
            return False

        except Exception as e:
            return e

    
    @api.model
    def setDefaultAddr(self, vals):
        pid = int(vals.get('addr_id'))
        partner = self.browse(pid)
        removeDefault = self.search([('type','=',partner.type),('parent_id','=',partner.parent_id.id)])
        removeDefault.is_default_addr = False
        partner.is_default_addr = True
        return True
    
    # @api.constrains('mobile','email') TODO:FIX
    # def _identify_same_partner(self):
    #     ''' Makes sure that no two partners have same mobile / email - For login with OTP purpose '''
    #     if not self.parent_id:
    #         if self.mobile and self.search([('id', '!=', self.id), ('mobile', '=', self.mobile), ('parent_id', '=',
    #                                                                                               False),('company_type','=','person')]).ids:
    #             raise ValidationError(_('Mobile No. already exists!!'))
    #         if self.email and self.search([('id', '!=', self.id), ('email', '=', self.email), ('parent_id', '=',
    #                                                                                            False),
    #                                        ('company_type','=','person')]).ids:
    #             raise ValidationError(_('Email already exists!!'))

    def send_otp(self, User, OTPType, Type, NonUserVal):

        Company = self.env.company or self.env['res.company'].browse(1)
        MobVal, EmailVal = '', ''
        OutgSMS = bool(self.env['ir.config_parameter'].sudo().get_param('bs.outgng_sms', False))
        OutgMail = bool(self.env['ir.config_parameter'].sudo().get_param('bs.outgng_mail', False))
        BSOTPExpTime = int(request.env['ir.config_parameter'].sudo().get_param('bs.otp_expiry_time', 120))

        totp = request.session.get('otpobj')
        if not (totp and ((datetime.now() - totp.time_generated).total_seconds() < BSOTPExpTime)):
            base32Code = pyotp.random_base32()
            totp = pyotp.TOTP(base32Code, interval=3600)
            request.session['otpobj'] = totp
            totp.time_generated = datetime.now()
        OTP = totp.now()

        Response = False

        if Type == 'email': EmailVal = User.login or User.partner_id.email if User else NonUserVal
        if Type == 'mobile': MobVal = User.partner_id.mobile if User else NonUserVal
        if Type == 'verify': MobVal = User.partner_id.mobile if User else NonUserVal

        if OTPType == 'login': SMSTemplate = self.env.ref('builderbay.bs_login_otp').content
        elif OTPType == 'signup': SMSTemplate = self.env.ref('builderbay.bs_signup_otp').content
        elif OTPType == 'reset_password': SMSTemplate = self.env.ref('builderbay.bs_reset_pass_otp').content
        else: SMSTemplate = False

        try:
            if Type == 'mobile' and SMSTemplate and MobVal:
                Message = str(SMSTemplate)%('mobile', OTP, BSOTPExpTime, Company.phone)
                url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s"%(Company.sms_apikey)
                headers = {'Authorization': 'Bearer %s' %(Company.get_sms_token())}
                params = {
                    "msisdn": MobVal,
                    "sms": Message,
                    "unicode": "0",
                    "senderid": Company.sms_senderid,
                    "pingbackurl": "https://builderbay.com/pingback/sms"
                }
                if OutgSMS: Response = requests.post(url, params, headers=headers)
                else: Response = True
            elif Type == 'email' and SMSTemplate and EmailVal:
                subject = (OTPType.title() + ' OTP') if not OTPType == 'reset_password' else 'Reset Password'
                Message = str(SMSTemplate)%('email', OTP, BSOTPExpTime, Company.phone)
                mail_values = { 'email_from' : 'info@builderbay.com',
                                'email_to' : EmailVal,
                                'subject' : subject,
                                'body_html' : Message,
                                'state' : 'outgoing'}
                mail = self.env['mail.mail'].sudo().create(mail_values)
                if OutgMail: mail.sudo().send(True)
                Response = True
            elif Type == 'verify' and SMSTemplate and MobVal:
                Message = str(SMSTemplate)%('mobile', OTP, BSOTPExpTime, Company.phone)
                url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s"%(Company.sms_apikey)
                headers = {'Authorization': 'Bearer %s' %(Company.get_sms_token())}
                params = {
                    "msisdn": MobVal,
                    "sms": Message,
                    "unicode": "0",
                    "senderid": Company.sms_senderid,
                    "pingbackurl": "https://builderbay.com/pingback/sms"
                }
                Response = requests.post(url, params, headers=headers)
                Response = {'response':Response,'otp':OTP}

        except Exception as e:
            print('Exception --- ', e)

        self.env['bs.sms.log'].sudo().create({'res_id':User.id if User else False, 'model':'res.users',
                'sms_type':'otp', 'subtype':'signin', 'body':Message, 'sent_time': datetime.now(),
                'recipient_id': User.partner_id.id if User else False, 'email': EmailVal, 'mobile': MobVal,
                'response':Response, 'otp':OTP })
        return Response

    def generate_ban_code(self):
        for rec in self:
            if not rec.parent_id:
                if not rec.partner_code:
                    if rec.supplier_rank > rec.customer_rank :
                        rec.partner_code = self.env['ir.sequence'].next_by_code('bs.vendor.code')
                    else:
                        if rec.customer_type == 'b2c':
                            rec.partner_code = self.env['ir.sequence'].next_by_code('bs.b2c.code')
                        else:
                            if rec.company_type == 'company' and rec.vat:
                                rec.partner_code = self.env['ir.sequence'].next_by_code('bs.partner.code')

                if rec.partner_code and not rec.bs_acct_no and self.env.company.corporate_code: #rec.company_type == 'company' and rec.vat -- removed
                    rec.bs_acct_no = self.env.company.corporate_code + rec.partner_code
                    rec.bs_acct_bank_id = self.env.company.bank_id.id
                    rec.bs_acct_ifsc_code = self.env.company.ifsc_code
                    rec.bs_acct_address = self.env.company.bank_address
                    rec.bs_acct_beneficiary_name = rec.name

    # ------------VENDOR ---- STARTS --------------------
    @api.model
    def redirect_action(self, args):
        action = self.env.ref('builderbay.purchase_rfq_vendor')
        action.sudo().domain = [('partner_id', '=', self.env.user.partner_id.id), ('state', '=', 'draft')]
        url = '/web#action=' + str(action.id) + '&model=purchase.order&view_type=list&cids=1&menu_id=340'
        return url

    @api.model
    def redirect_action_confirm(self, args):
        action = self.env.ref('builderbay.purchase_confirm_vendor')
        action.sudo().domain = [('partner_id', '=', self.env.user.partner_id.id), ('state', '=', 'purchase')]
        url = '/web#action=' + str(action.id) + '&model=purchase.order&view_type=list&cids=1&menu_id=340'
        return url

    @api.model
    def redirect_action_cancel(self, args):
        action = self.env.ref('builderbay.purchase_cancel_vendor')
        action.sudo().domain = [('partner_id', '=', self.env.user.partner_id.id), ('state', '=', 'cancel')]
        url = '/web#action=' + str(action.id) + '&model=purchase.order&view_type=list&cids=1&menu_id=340'
        return url
    # ------------VENDOR ---- ENDS --------------------


class BSResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    ifsc_code = fields.Char(string="IFSC Code")
    bank_address = fields.Text(string="Bank Address")
    bank_attachment_id = fields.Many2one('ir.attachment', string="Cancelled Cheque or Bank Statement")
    is_default = fields.Boolean('Is Default ?')
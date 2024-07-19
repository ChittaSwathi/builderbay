from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_users import SignupError
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import datetime
from datetime import datetime


class BSSignup(AuthSignupHome):


    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        qcontext.update({'name': qcontext.get('fname', '') + ' ' + qcontext.get('lname', ''),
                         'login': qcontext.get('email') or qcontext.get('mobile'),
                         'customer_type': 'b2b' if qcontext.get('b2b') == 'on' else 'b2c',
                         'password':qcontext.get('password') or qcontext.get('confirm_password')})
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'customer_type')}
        if not values: raise UserError(_("The form was not properly filled in."))
        values['groups_id'] = [(6, 0, [request.env.ref('base.group_portal').id])]
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '').split('_')[0]
        if lang in supported_lang_codes: values['lang'] = lang
        self._signup_with_values(qcontext.get('token'), values)

        User = request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))])
        CompanyRec, DistrictID, StateID = False, False, False

        if int(qcontext.get('district_id')) != 0:
            DistrictID =  int(qcontext.get('district_id'))
        elif int(qcontext.get('gst_district_id')) != 0:
            DistrictID = int(qcontext.get('gst_district_id'))

        if int(qcontext.get('state_id')) != 0:
            StateID = int(qcontext.get('state_id'))
        elif int(qcontext.get('gst_state_id')) != 0:
            StateID = int(qcontext.get('gst_state_id'))


        if User:
            Contact, Company = {'customer_type': 'b2c',
                                'email': qcontext.get('email') or qcontext.get('login'),
                                'zip': qcontext.get('zip'),
                                'city': qcontext.get('city'),
                                'district_id': DistrictID,
                                'state_id': StateID,
                                'mobile': qcontext.get('mobile'),}, {}
            if qcontext.get('b2b') == 'on':
                CustTags = []

                Company.update({'company_type': 'company', 'is_company':True})

                if qcontext.get('builder') == 'on': CustTags += [request.env.ref('builderbay.builder_id').id]
                if qcontext.get('rmc') == 'on': CustTags += [request.env.ref('builderbay.rmc_id').id]
                if qcontext.get('manufacturer') == 'on': CustTags += [request.env.ref('builderbay.manufacturer_id').id]
                if qcontext.get('dealer') == 'on': CustTags += [request.env.ref('builderbay.dealer_id').id]
                if qcontext.get('others') == 'on': CustTags += [request.env.ref('builderbay.others_id').id]
                Company.update({'category_id': [(6, 0, CustTags)]})

                Company.update({'vat': qcontext.get('gstin').strip(),
                                'state_id': StateID,
                                'district_id': DistrictID,
                                'city': qcontext.get('gst_city'),
                                'zip': qcontext.get('gst_zip'),
                                'street': qcontext.get('reg_address'),
                                'name': qcontext.get('shop_name'),#trade name
                                'legal_name': qcontext.get('legal_name'),
                                'l10n_in_gst_treatment': 'regular',
                                })
                CompanyRec = request.env['res.partner'].sudo().search([('vat', '=', qcontext.get('gstin', '').strip())],limit=1)
                if not CompanyRec: CompanyRec = request.env['res.partner'].sudo().create(Company)
                else: CompanyRec.write(Company)

            if CompanyRec:
                Contact.update({'customer_type': 'b2b', 'type':'contact', 'parent_id': CompanyRec.id})
            User.partner_id.sudo().write(Contact)

        request.env.cr.commit()

    @http.route('/bs/default/address', type='json', auth="user", sitemap=False, website=True)
    def bs_signup_address(self, **kw):
        Partner = request.env.user.partner_id
        return Partner.sudo().write(kw)


    @http.route('/bs/user/authenticate', type='json', auth="none", sitemap=False, website=True)
    def bs_user_authenticate(self, **kw):
        """ Validates and authenticates if a user account exists or not, based on both email and mobile """
        db, login, password, type = kw.get('db',request.env.cr.dbname), kw.get('login'), kw.get('password'),kw.get('type','email')
        RedirectingURL =  kw.get('url').split('?redirect=')[-1] \
                            if (kw.get('url','') and '?redirect=' in kw.get('url','')) else ''

        if db and login and password:
            if type == 'email':
                User = request.env['res.users'].sudo().search([('login','=',login)],limit=1)
            else: #mobile
                User = request.env['res.users'].sudo().search([('login','=',login)],limit=1) #if user uses mobile to login
                if not User: User =  request.env['res.users'].sudo().search([('partner_id.mobile','=',login)], limit=1)

            # if not User.partner_id.zip: RedirectingURL = '/my/address'
            if User:
                try: Response = {'uid':request.session.authenticate(db, User.login, password), 'error':'',
                                 'redirect_url': RedirectingURL}
                except: Response = {'uid':User.id, 'error':'Invalid Credentials', 'redirect_url': ''}
            else:
                Response= {'uid':False, 'error':'Account Not Found!', 'redirect_url': ''}
        return Response

    @http.route('/send/login/otp', type='json', auth="none", sitemap=False, website=True)
    def bs_send_login_otp(self, **kw):
        print('send login otp',kw)
        Value, Type, OTPType = kw.get('login', False), kw.get('type', False), kw.get('otp_type', False)
        User = self.get_user_id(Type, Value)
        if User:
            OTPSent = request.env['res.partner'].send_otp(User, OTPType, Type, Value)
            if OTPSent: return {'uid': User.id, 'error': ''} #TODO:check otp response
            else: return {'uid': User.id, 'error': 'Something went wrong !!'}
        else:
            return {'uid': False, 'error': 'Account Not Found. Please signup !!'}

    @http.route('/send/signup/otp', type='json', auth="none", sitemap=False, website=True)
    def bs_send_signup_otp(self, **kw):
        print('send signup otp', kw)
        Value, Type, OTPType = kw.get('login', False), kw.get('type', False), kw.get('otp_type', False)
        User = self.get_user_id(Type, Value)
        if User:
            return {'uid': User.id,  'error':'Account already exists. Please login !!'}
        else:
            OTPSent = request.env['res.partner'].send_otp(False, OTPType, Type, Value)
            if OTPSent: return {'uid': False, 'error': ''}
            else: return {'uid': False, 'error': 'Something went wrong !!'}

    def get_user_id(self, Type, Value):
        '''Returns user id based on the type (email/mobile) and its respective value'''
        if Type and Value:
            if Type == 'email':
                User = request.env['res.users'].sudo().search([('login', '=', Value)], limit=1)
            else:  # mobile
                User = request.env['res.users'].sudo().search([('login', '=', Value)],limit=1)  # if user uses mobile to login
                if not User: User = request.env['res.users'].sudo().search([('partner_id.mobile', '=', Value)], limit=1)
            return User
        else: return False

    @http.route(['/bs/validate/otp'], type='json', auth="public", methods=['POST'],sitemap=False, website=True)
    def verify_otp(self, otp=False):
        totp = request.session.get('otpobj')
        BSOTPExpTime = int(request.env['ir.config_parameter'].sudo().get_param('bs.otp_expiry_time', 120))
        if totp:
            TotalSecs = (datetime.now() - totp.time_generated).total_seconds()
            if TotalSecs < BSOTPExpTime:
                return totp.verify(otp)
            else:
                return False # OTPExpired
        else:
            return False # OTPNotFound in session

    @http.route('/bs/user/login', type='json', auth="none", sitemap=False, website=True)
    def user_login(self, **kw):
        # TODO: Force Login user from backend
        return http.local_redirect(self._login_redirect(kw.get('uid')), keep_hash=True)

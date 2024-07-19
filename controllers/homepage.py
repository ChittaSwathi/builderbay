import odoo
from odoo import http, _
from odoo.http import request
from odoo.addons.website.controllers.main import Home
from odoo.addons.portal.controllers.web import Home as PortalHome
import werkzeug
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ensure_db
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.service import security

import logging
_logger = logging.getLogger(__name__)


class BSPortalHome(PortalHome):
    #overridden
    def _login_redirect(self, uid, redirect=None):
        if not redirect and not request.env['res.users'].sudo().browse(uid).has_group('base.group_user'):
            redirect = '/'
        return super(Home, self)._login_redirect(uid, redirect=redirect)

class BSWebHome(Home):

    @http.route('/', type='http', auth="public", website=True)
    def index(self, **kw) :#TODO:remove values
        Partner = request.env.user.partner_id
        homepageRec = request.env['bs.homepage'].sudo().search([('company_id', '=', request.env.company.id)], limit=1)
        best_selling = request.env['product.template'].sudo().search([('is_best_selling', '=', True)], order='web_display_seq desc')
        hot_deals = request.env['product.template'].sudo().search([('is_hot_deal', '=', True)], order='web_display_seq desc')
        sellers = request.env['res.partner'].sudo().search([('supplier_rank', '>=', 1)])
        brands = request.env['product.attribute.value'].sudo().search(
            [('attribute_id', '=', request.env.ref('builderbay.brand_attribute').id),
             ('customer_type', 'in', [Partner.customer_type, 'both'])])
        ClientReviews = request.env['bs.client.review'].sudo().search([])
        values = {'best_selling':best_selling,
                  'hot_deals':hot_deals,
                  'sellers':sellers,
                  'brands':brands,
                  'homepage': homepageRec,
                  'banner_ids': homepageRec.banner_ids if homepageRec else False,
                  'client_reviews' : [ClientReviews[i * 2:(i + 1) * 2] for i in range((len(ClientReviews) + 2 - 1) // 2 )],
                  'AllClientReviews': ClientReviews,
                  }
        return request.render('builderbay.bs_customer_homepage', values)

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        AllStates = request.env['res.country.state'].sudo().search([('country_id.code', '=', 'IN')])
        AllDistricts = request.env['bs.district'].sudo().search([])
        values['state_ids'] = AllStates
        values['district_ids'] = AllDistricts

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                print(request.params)
                if request.params['password'] and request.params['otpLogin'] != '1':
                    uid = request.session.authenticate(request.session.db,
                                                       request.params.get('login') or request.params.get(
                                                           'email') or request.params.get('mobile'),
                                                       request.params['password'])
                if not request.params['password'] or (request.params['password'] and request.params['otpLogin'] == '1'):
                    if request.params['first'] and request.params['second'] and request.params['third'] and \
                            request.params['fourth'] and request.params['five'] and request.params['six']:
                        otp = request.params['first'] + request.params['second'] + request.params['third'] + \
                              request.params['fourth'] + request.params['five'] + request.params['six']
                        wsgienv = request.httprequest.environ
                        env = dict(
                            base_location=request.httprequest.url_root.rstrip('/'),
                            HTTP_HOST=wsgienv['HTTP_HOST'],
                            REMOTE_ADDR=wsgienv['REMOTE_ADDR'],
                        )
                        uid = odoo.registry(request.session.db)['res.users'].authenticate_otp(request.session.db,
                                                                                              request.params['email'],
                                                                                              otp, env)
                        request.session.rotate = True
                        request.session.db = request.session.db
                        request.session.uid = uid
                        request.session.login = request.params['email']
                        request.session.session_token = uid and security.compute_session_token(request.session,
                                                                                               request.env)
                        request.uid = uid
                        request.disable_db = False

                        if uid: request.session.get_context()
                request.params['login_success'] = True
                return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employee can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        if request.session.get('uid'):
            return False

        response = request.render('auth_signup.signup', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                    )
                    template = request.env.ref('auth_signup.mail_template_user_signup_account_created',
                                               raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().with_context(
                            lang=user_sudo.lang,
                            auth_login=werkzeug.url_encode({'auth_login': user_sudo.email}),
                        ).send_mail(user_sudo.id, force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.name or e.value
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")
        AllStates = request.env['res.country.state'].sudo().search([('country_id.code', '=', 'IN')])
        AllDistricts = request.env['bs.district'].sudo().search([])
        qcontext['state_ids'] = AllStates
        qcontext['district_ids'] = AllDistricts

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/reset/password', type='http', auth='public', website=True, sitemap=False)
    def bs_reset_password(self, **kw):
        Values ={}
        return request.render('builderbay.bs_reset_password', Values)

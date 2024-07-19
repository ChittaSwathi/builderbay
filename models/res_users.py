from odoo import api, fields, models, _,SUPERUSER_ID,registry
from odoo.http import request
from odoo.exceptions import AccessDenied
import re
import logging
_logger = logging.getLogger(__name__)

from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG

from lxml import etree
from lxml.builder import E

def name_selection_groups(ids):
    return 'sel_groups_' + '_'.join(str(it) for it in ids)

def name_boolean_group(id):
    return 'in_group_' + str(id)

class BSResUsers(models.Model):
    _inherit = "res.users"

    otp = fields.Char(string="OTP", copy=False)
    user_type = fields.Selection([('customer', 'Customer'),
                                 ('vendor', 'Vendor'),
                                 ('sp', 'Sales Person'),
                                 ('dp', 'Delivery Person')], string="User Type")

    def _check_credential(self, otp):
        """ Validates the current user's otp.

        Override this method to plug additional authentication methods.

        Overrides should:

        * call `super` to delegate to parents for credentials-checking
        * catch AccessDenied and perform their own checking
        * (re)raise AccessDenied if the credentials are still invalid
          according to their own validation method

        When trying to check for credentials validity, call _check_credentials
        instead.
        """
        """ Override this method to plug additional authentication methods"""
        assert otp
        valid = self.search([('otp', '=', otp)])
        if not valid:
            raise AccessDenied()

    @classmethod
    def _login_otp(cls, db, login, otp):
        if not otp:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth():
                    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
                    if (re.search(regex, login)):
                        user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
                    else:
                        user = request.env['res.users'].sudo().search([('partner_id.mobile', '=', login)], limit=1)
                    if not user:
                        raise AccessDenied()
                    user = user.with_user(user)
                    #                     user._check_credential(otp)
                    user._update_last_login()
        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from %s", db, login, ip)
            raise

        _logger.info("Login successful for db:%s login:%s from %s", db, login, ip)

        return user.id

    @classmethod
    def authenticate_otp(cls, db, login, otp, user_agent_env):
        """Verifies and returns the user ID corresponding to the given
          ``login`` and ``password`` combination, or False if there was
          no matching user.
           :param str db: the database on which user is trying to authenticate
           :param str login: username
           :param str password: user password
           :param dict user_agent_env: environment dictionary describing any
               relevant environment attributes
        """
        uid = cls._login_otp(db, login, otp)
        if user_agent_env and user_agent_env.get('base_location'):
            with cls.pool.cursor() as cr:
                env = api.Environment(cr, uid, {})
                if env.user.has_group('base.group_system'):
                    # Successfully logged in as system user!
                    # Attempt to guess the web base url...
                    try:
                        base = user_agent_env['base_location']
                        ICP = env['ir.config_parameter']
                        if not ICP.get_param('web.base.url.freeze'):
                            ICP.set_param('web.base.url', base)
                    except Exception:
                        _logger.exception("Failed to update web.base.url configuration parameter")
        return uid

    @classmethod
    def check_otp(cls, db, uid, otp):
        """Verifies that the given (uid, password) is authorized for the database ``db`` and
           raise an exception if it is not."""
        if not otp:
            # empty passwords disallowed for obvious security reasons
            raise AccessDenied()
        db = cls.pool.db_name
        if cls.__uid_cache[db].get(uid) == otp:
            return
        cr = cls.pool.cursor()
        try:
            self = api.Environment(cr, uid, {})[cls._name]
            with self._assert_can_auth():
                self._check_credential(otp)
                cls.__uid_cache[db][uid] = otp
        finally:
            cr.close()

    @api.model
    def update_user(self, vals):
        user = self.env.user
        partner = self.env.user.partner_id
        user.login = vals.get('email').strip()
        if vals.get('password') != '_______1____':
            user.password = vals.get('password').strip()
        partner.name= vals.get('name').strip()
        partner.mobile= vals.get('mobile').strip()
        return True
        
        
class BSResGroups(models.Model):
    _inherit = "res.groups"

    @api.model
    def _update_user_groups_view(self):
        GrpExists = True
        try:
            DisplayContacts = self.env.ref('builderbay.group_display_contacts').id
            DisplayCRM = self.env.ref('builderbay.group_display_crm').id
            DisplaySales = self.env.ref('builderbay.group_display_sales').id
            DisplayWebsite = self.env.ref('builderbay.group_display_website').id
            DisplaySign = self.env.ref('builderbay.group_display_sign').id
            DisplayPurchase = self.env.ref('builderbay.group_display_purchase').id
            DisplayHelpdesk = self.env.ref('builderbay.group_display_helpdesk').id
            DisplayLinkTracker = self.env.ref('builderbay.group_display_linktracker').id
            DisplayInventory = self.env.ref('builderbay.group_display_inventory').id
            DisplayAccounting = self.env.ref('builderbay.group_display_accounting').id
            DisplayPayroll = self.env.ref('builderbay.group_display_payroll').id
            DisplayEmployee = self.env.ref('builderbay.group_display_employees').id
        except:
            DisplayContacts, DisplayCRM, DisplaySales,DisplayWebsite, DisplaySign, DisplayPurchase, DisplayHelpdesk, \
            DisplayLinkTracker, DisplayInventory, DisplayAccounting, DisplayPayroll, DisplayEmployee = 0,0,0,0,0,0,0,0,0,0,0,0
            GrpExists = False

        """ Modify the view with xmlid ``base.user_groups_view``, which inherits
            the user form view, and introduces the reified group fields.
        """
        # remove the language to avoid translations, it will be handled at the view level
        self = self.with_context(lang=None)

        # We have to try-catch this, because at first init the view does not
        # exist but we are already creating some basic groups.
        view = self.env.ref('base.user_groups_view', raise_if_not_found=False)
        if not (view and view.exists() and view._name == 'ir.ui.view'):
            return

        if self._context.get('install_filename') or self._context.get(MODULE_UNINSTALL_FLAG):
            # use a dummy view during install/upgrade/uninstall
            xml = E.field(name="groups_id", position="after")

        else:
            group_no_one = view.env.ref('base.group_no_one')
            group_employee = view.env.ref('base.group_user')
            xml1, xml2, xml3 = [], [], []
            xml_by_category = {}
            xml1.append(E.separator(string='User Type', colspan="2", groups='base.group_no_one'))

            user_type_field_name = ''
            user_type_readonly = str({})
            sorted_tuples = sorted(self.get_groups_by_application(),
                                   key=lambda t: t[0].xml_id != 'base.module_category_user_type')
            for app, kind, gs, category_name in sorted_tuples:  # we process the user type first

                # Menu Control:
                IsDisplayGroupSet = False
                if GrpExists:

                    if app.name == 'Contacts':
                        IsDisplayGroupSet = name_boolean_group(DisplayContacts)
                    elif app.name == 'CRM':
                        IsDisplayGroupSet = name_boolean_group(DisplayCRM)
                    elif app.name == 'Sales':
                        IsDisplayGroupSet = name_boolean_group(DisplaySales)
                    elif app.name == 'Website':
                        IsDisplayGroupSet = name_boolean_group(DisplayWebsite)
                    elif app.name == 'Sign':
                        IsDisplayGroupSet = name_boolean_group(DisplaySign)
                    elif app.name == 'Purchase':
                        IsDisplayGroupSet = name_boolean_group(DisplayPurchase)
                    elif app.name == 'Helpdesk':
                        IsDisplayGroupSet = name_boolean_group(DisplayHelpdesk)
                    elif app.name == 'Link Tracker':
                        IsDisplayGroupSet = name_boolean_group(DisplayLinkTracker)
                    elif app.name == 'Inventory':
                        IsDisplayGroupSet = name_boolean_group(DisplayInventory)
                    elif app.name == 'Accounting':
                        IsDisplayGroupSet = name_boolean_group(DisplayAccounting)
                    elif app.name == 'Payroll':
                        IsDisplayGroupSet = name_boolean_group(DisplayPayroll)
                    elif app.name == 'Employees':
                        IsDisplayGroupSet = name_boolean_group(DisplayEmployee)
                    else:
                        IsDisplayGroupSet = False

                attrs = {}
                # hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
                if app.xml_id in self._get_hidden_extra_categories():
                    attrs['groups'] = 'base.group_no_one'

                # User type (employee, portal or public) is a separated group. This is the only 'selection'
                # group of res.groups without implied groups (with each other).
                if app.xml_id == 'base.module_category_user_type':
                    # application name with a selection field
                    field_name = name_selection_groups(gs.ids)
                    user_type_field_name = field_name
                    user_type_readonly = str({'readonly': [(user_type_field_name, '!=', group_employee.id)]})
                    attrs['widget'] = 'radio'
                    attrs['groups'] = 'base.group_no_one'
                    xml1.append(E.field(name=field_name, **attrs))
                    if IsDisplayGroupSet: xml_by_category.append(E.div(E.field(name=IsDisplayGroupSet)))
                    xml1.append(E.newline())

                elif kind == 'selection':
                    # application name with a selection field
                    field_name = name_selection_groups(gs.ids)
                    attrs['attrs'] = user_type_readonly
                    if category_name not in xml_by_category:
                        xml_by_category[category_name] = []
                        xml_by_category[category_name].append(E.newline())
                    xml_by_category[category_name].append(E.field(name=field_name, **attrs))

                    xml_by_category[category_name].append(E.newline())

                else:
                    # application separator with boolean fields
                    app_name = app.name or 'Other'
                    xml3.append(E.separator(string=app_name, colspan="4", **attrs))
                    attrs['attrs'] = user_type_readonly
                    for g in gs:
                        field_name = name_boolean_group(g.id)
                        if g == group_no_one:
                            # make the group_no_one invisible in the form view
                            xml3.append(E.field(name=field_name, invisible="1", **attrs))
                        else:
                            xml3.append(E.field(name=field_name, **attrs))

            xml3.append({'class': "o_label_nowrap"})
            if user_type_field_name:
                user_type_attrs = {'invisible': [(user_type_field_name, '!=', group_employee.id)]}
            else:
                user_type_attrs = {}

            for xml_cat in sorted(xml_by_category.keys(), key=lambda it: it[0]):
                master_category_name = xml_cat[1]
                xml2.append(E.group(*(xml_by_category[xml_cat]), col="2", string=master_category_name))

            xml = E.field(
                E.group(*(xml1), col="2"),
                E.group(*(xml2), col="2", attrs=str(user_type_attrs)),
                E.group(*(xml3), col="4", attrs=str(user_type_attrs)), name="groups_id", position="replace")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))

        # serialize and update the view
        xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")
        if xml_content != view.arch:  # avoid useless xml validation if no change
            new_context = dict(view._context)
            new_context.pop('install_filename', None)  # don't set arch_fs for this computed view
            new_context['lang'] = None
            view.with_context(new_context).write({'arch': xml_content})

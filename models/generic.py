from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.http import request
import datetime
from datetime import datetime, date
import ast
import copy
import json
import io
import logging
from . import BSnum2words
import lxml.html
import ast
from collections import defaultdict
from math import copysign
import pprint
from email.policy import default
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


from dateutil.relativedelta import relativedelta

from odoo.tools.misc import xlsxwriter
from odoo import models, fields, api, _
from odoo.tools import config, date_utils, get_lang
from odoo.osv import expression
from babel.dates import get_quarter_names
from odoo.tools.misc import formatLang, format_date
from odoo.addons.web.controllers.main import clean_action
from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)

class BSView(models.Model):
    _inherit = 'ir.ui.view'
    
    def check_user_group(self):
        # x = request.website.is_publisher()
        if request.env.user and request.session.uid and (not request.env.user.has_group('base.group_portal')):
            return True
        return False

    # Overridden: For Header & Footer
    @api.model
    def _prepare_qcontext(self):
        """ Returns the qcontext : rendering context with website specific value (required
            to render website layout template)
        """
        qcontext = super(BSView, self)._prepare_qcontext()

        if request and getattr(request, 'is_frontend', False):
            Website = self.env['website']
            editable = request.website.is_publisher()
            translatable = editable and self._context.get('lang') != request.env['ir.http']._get_default_lang().code
            editable = not translatable and editable

            cur = Website.get_current_website()
            if self.env.user.has_group('website.group_website_publisher') and self.env.user.has_group(
                    'website.group_multi_website'):
                qcontext['multi_website_websites_current'] = {'website_id': cur.id, 'name': cur.name,
                                                              'domain': cur._get_http_domain()}
                qcontext['multi_website_websites'] = [
                    {'website_id': website.id, 'name': website.name, 'domain': website._get_http_domain()}
                    for website in Website.search([]) if website != cur
                ]

                cur_company = self.env.company
                qcontext['multi_website_companies_current'] = {'company_id': cur_company.id, 'name': cur_company.name}
                qcontext['multi_website_companies'] = [
                    {'company_id': comp.id, 'name': comp.name}
                    for comp in self.env.user.company_ids if comp != cur_company
                ]
            Partner = self.env.user.partner_id
            # Banners = self.env.company.banner_ids
            homepageRec = self.env['bs.homepage'].sudo().search([('company_id','=',self.env.company.id)],limit=1)
            FooterLinks = homepageRec.footer_link_ids if homepageRec else False
            HeaderSearchData =  homepageRec.header_search_ids if homepageRec else False

            eCommCategs = self.env['product.public.category'].search([('parent_id', '=', False),
                                                              ('customer_type', 'in',[Partner.customer_type, 'both'])])
            ShippingIds = {'default':{} , 'others':{}}
            if Partner.default_shipping_id:
                ShippingIds.update({'default': {Partner.default_shipping_id.id: str(Partner.default_shipping_id.city) + ' - ' + str(
                    Partner.default_shipping_id.zip)}})
            elif Partner.city or Partner.zip:
                ShippingIds.update({'default': {Partner.id : str(Partner.city) + ' - ' + str(Partner.zip)}})

            if Partner.child_ids.filtered(lambda x: x.type == 'delivery'):
                OtherAddress = {Partner.id : str(Partner.city) + ' - ' + str(Partner.zip)}
                for i in Partner.child_ids.filtered(lambda x: x.type == 'delivery'):
                    OtherAddress.update({i.id : str(i.city) + ' - ' + str(i.zip) })
                ShippingIds.update(others = OtherAddress)

            NotificationsCount = self.env['bs.notification'].sudo().search_count([('partner_id','=',Partner.id),('read','=',False)])
            Notifications = self.env['bs.notification'].sudo().search([('partner_id','=',Partner.id)], order="id desc")
            qcontext.update(dict(
                brands = self.env['product.attribute.value'].sudo().search([('attribute_id', '=', self.env.ref('builderbay.brand_attribute').id)]),
                main_object=self,
                website=request.website,
                is_view_active=request.website.is_view_active,
                res_company= request.website.company_id.sudo(),
                translatable=translatable,
                editable=editable,

                footer_links = FooterLinks,
                mega_menu = eCommCategs.filtered(lambda x:x.megamenu).sorted(lambda x: x.megamenu_sequence),
                mega_brands = self.get_all_brands(),
                header_search =HeaderSearchData,
                shipping_ids = ShippingIds,
                total_orders = self.env['sale.order'].sudo().search_count([('partner_id', '=', request.env.user.partner_id.id),
                              ('state', '=', 'sent'),('show_in_cart','=',True),('payment_processed','=',False)]) or 0,
                customer_type = Partner.customer_type if Partner else False,
                customer = Partner if Partner else False,
                gstin = (Partner.vat if not Partner.parent_id else Partner.parent_id.vat) if Partner else '',
                default_shipping_id = Partner.default_shipping_id if Partner.default_shipping_id else Partner,
                so_reject_reasons = request.env['bs.rejection.reason'].sudo().search([]),
                BrandAttrID = request.env.ref('builderbay.brand_attribute').id,
                notifications_count = NotificationsCount,
                notifications = Notifications,
            ))
        return qcontext

    def get_all_brands(self):
        """ Fetches all brands from ecommerce categories (including sub categories) """
        AllBrands = {}
        Partner = self.env.user.partner_id
        eCommObj = self.env['product.public.category']

        for eCatag in eCommObj.search([('customer_type','in',[Partner.customer_type, 'both'])]):
            ProductIDs = self.env['product.template'].search(['|', ('public_categ_ids', 'child_of', int(eCatag.id)),
                                                              ('public_categ_ids', '=', int(eCatag.id))]).ids
            Brands = self.env['product.template.attribute.line'].search(
                    [('attribute_id', '=', self.env.ref('builderbay.brand_attribute').id),
                     ('product_tmpl_id', 'in', ProductIDs)]).mapped('value_ids').filtered(lambda x: x.is_top_brand == True)
            AllBrands[eCatag] = Brands
        return AllBrands

class BSEcommCategories(models.Model):
    _inherit = "product.public.category"
    
    def get_redirect_url(self,products,product):
        for k, v in products.items():
            if v == product:
                return self.env['product.template'].browse(int(k))
        return False
    
    def get_sorted_brand(self, products):
        ProdVariants = products.mapped('attribute_line_ids').filtered(lambda x: x.attribute_id.id == self.env.ref('builderbay.brand_attribute').id)
        sortedBrand = ProdVariants.mapped('value_ids').sorted(lambda x: x.position)
        return sortedBrand

    def get_recursive_url(self, URL="/"):
        if self.parent_id:
            URL = self.parent_id.get_recursive_url(URL) + '/' + slug(self)
        else:
            if URL == '/': URL += slug(self)
            else: URL += slug(self)
        return URL
    
    def get_cdn_url_brand(self, brand):
        final_uri_preview = "/web/static/src/img/placeholder.png"
        try:
            from werkzeug import urls
            import requests
            s3 = ['brand']
            Website_env = self.env['website']
            website = Website_env.get_current_website()
            cdn_url = website.cdn_url
            if cdn_url:
                s3.append(slug(brand))
                uri = '/'.join(s3)
                final_uri = urls.url_join(cdn_url, uri)
                response = requests.get(final_uri)
                if response.status_code != 200:
                    homepage = self.env['bs.homepage'].search([],limit=1)
                    return final_uri_preview
                return final_uri
            else:
                return final_uri_preview
        except:
            pass
        return final_uri_preview
    
    def get_cdn_url(self, URL="/"):
        final_uri_preview = "/web/static/src/img/placeholder.png"
        try:
            from werkzeug import urls
            import requests
            s3 = ['category']
            
            Website_env = self.env['website']
            website = Website_env.get_current_website()
            cdn_url = website.cdn_url
            if cdn_url:
                s3.append(slug(self))
                uri = '/'.join(s3)
                final_uri = urls.url_join(cdn_url, uri)
                response = requests.get(final_uri)
                if response.status_code != 200:
                    homepage = self.env['bs.homepage'].search([],limit=1)
                    return final_uri_preview
                return final_uri
            else:
                return final_uri_preview
        except:
            pass
        return final_uri_preview
            
        

    def _domain_brands(self):
        return [('attribute_id', '=', self.env.ref('builderbay.brand_attribute').id)]

    @api.depends('create_date', 'write_date', 'name')
    def _compute_slug(self):
        for categ in self:
            if categ.id: categ.update({'category_slug':slug(categ)})

    categ_type_ids = fields.Many2many('ecomm.categ.type','ecomm_categ_type_rel', 'categ_id', 'type_id', string='Type')
    banner_ids = fields.One2many('banner.image', 'ecomm_id', string='Banners')
    banner_s3_url = fields.One2many('banner.image.s3', 'ecomm_id', string='Banners')

    # Used in Header search/megamenu, l1 listing page (Category specific page)
    top_brand_ids = fields.Many2many('product.attribute.value','ecomm_top_brand_rel','ecomm_id','brand_id',string="Top Brands",
                                     domain=_domain_brands)
    top_vendor_ids = fields.Many2many('res.partner','ecomm_top_vendor_rel','ecomm_id','vendor_id',string="Top Vendors",
                                      domain=[('supplier_rank','>',0)])
    specification_ids = fields.One2many('product.template.attribute.line','ecomm_id','Specifications')
    search_id = fields.Many2one('res.company')
    pdp_template_id = fields.Many2one('ir.ui.view', string="View Template")
    is_coming_soon = fields.Boolean("Is coming soon?")
    upload_enq1_id = fields.Many2one('bs.enquiry')
    upload_enq2_id = fields.Many2one('bs.enquiry')

    allcategs_image = fields.Image("Image", max_width=128, max_height=128, help="This image will be displayed in all categories page like construction, industrial etc.")
    megamenu = fields.Boolean('Show in Megamenu')
    megamenu_sequence = fields.Integer('Megamenu Sequence', help="Sequence for displaying Megamenu in website.")

    products_description = fields.Html('Products Description')
    customer_type = fields.Selection([('b2b', 'B2B'),
                                      ('b2c', 'B2C'),
                                      ('both', 'Both')], string='Customer Type', default="both")
    l2_view = fields.Selection([('tile_view', 'Tile View'),
                                ('brand_view', 'Brands View'),
                                ('ecomm_view', 'eCommerce View')], string="L2 View")
    is_trending = fields.Boolean("Is Trending?")
    category_slug = fields.Char(string="Slug", copy=False, help="S3 bucket name same as Slug", compute = '_compute_slug', store=True)
    detailed_info = fields.Html('Category Information')

    @api.onchange('products_description')
    def _onchange_products_description(self):
        if self.products_description:
            self.env['product.template'].search([('public_categ_ids','child_of',[self._origin.id]),
                                                 ('website_description','in', ['<p><br></p>', '<p><br> </p>', '<p><br /></p >'])]).\
                write({'website_description':self.products_description})

    def get_brands(self, eCommCategIDs):
        ProductIDs, Brands = [], []
        for categ in eCommCategIDs:
            ProductIDs += self.env['product.template'].search(['|', ('public_categ_ids', 'child_of', int(categ)),
                                                          ('public_categ_ids', '=', int(categ))]).ids
            Brands += self.env['product.template.attribute.line'].search(
                [('attribute_id', '=', self.env.ref('builderbay.brand_attribute').id),
                 ('product_tmpl_id', 'in', ProductIDs)]).mapped('value_ids')
        return self.env['product.attribute.value'].browse(list(set([brand.ids if len(brand) >1 else brand.id for brand in Brands])))

class BSEcommCategs3(models.Model):
    _name = "banner.image.s3"
    _description = 'Ecommerce Category s3 url link'

    name = fields.Char('Name')
    ecomm_id = fields.Many2one('product.public.category')

class BSEcommCategType(models.Model):
    _name = "ecomm.categ.type"
    _description = 'Ecommerce Category Type'

    name = fields.Char('Name', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Category type already exists !"),
    ]

class BSUom(models.Model):
    _inherit = 'uom.uom'

    data_type = fields.Selection([('int','Integer'),('float','Float')], string="Data Type") #for frontened UOM conversions

class BSDistrict(models.Model):
    _name = 'bs.district'

    name = fields.Char('Name')
    state_id = fields.Many2one('res.country.state', string="State")

class BSGSTDetails(models.Model):
    _name = "bs.gst"

    name = fields.Char('GSTIN')
    pan = fields.Char('PAN')
    registered_address = fields.Text('Registered Address')
    legal_name = fields.Char('Legal Name')
    trade_name = fields.Char('Trade Name')
    reg_date = fields.Date('Registered On')
    gst_updated_date = fields.Date('Last Updated On')
    api_response = fields.Text('API Response')
    gst_status = fields.Selection([('active','Active'),('inactive','InActive')], 'GST Status')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state', string="State")
    district_id = fields.Many2one('bs.district', string="District")
    pincode = fields.Char('Pincode')
    default = fields.Boolean("Default GSTIN")
    partner_id = fields.Many2one('res.partner', 'B2B Customer')
    mobile = fields.Char('Mobile')

    _sql_constraints = [
        ('unique_name', 'unique (name)', 'GSTIN already exists')
    ]

class BSHeaderSearch(models.Model):
    _name = "bs.header.search"
    _description = 'Header Search'
    _order = "sequence"

    name = fields.Char(string="Search Label")
    sequence = fields.Integer('Sequence', help="Sequence used to order header search")
    categ_ids = fields.Many2many('product.public.category','header_search_rel','categ_id','search_id', string="Categories")
    header_search_id = fields.Many2one('bs.homepage')

class BSClientReviews(models.Model):
    _name = "bs.client.review"
    _description = 'Client Review'
    _order = "sequence"

    name = fields.Char('Review Title')
    client_id = fields.Many2one('res.partner', string="Client")
    sequence = fields.Integer('Sequence', help="Sequence in which to show reviews")
    review = fields.Text('Review')
    review_id = fields.Many2one('bs.homepage')

class BSStockPicking(models.Model):
    _inherit = "stock.picking"

    status_date_details = fields.Char('Status Update')
    bs_pick_status = fields.Selection([('Order Placed','Order Placed'),('Packed','Packed'),('Dispatched','Dispatched'),('Out for Delivery','Out for Delivery'),('Delivered','Delivered')], string="Status", default="Order Placed")
    delivery_person = fields.Many2one(
        'res.users', 'Delivery Person', tracking=True,
        domain=[('user_type', '=', 'dp')],
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        default=lambda self: self.env.user)

    def create(self, vals):
        vals['status_date_details'] = 'Order Placed' +'___' + str(datetime.now())
        res = super(BSStockPicking, self).create(vals)
        return res

    def write(self, vals):
        if 'bs_pick_status' in vals:
            vals['status_date_details'] = self.status_date_details + '___' + vals['bs_pick_status'] + '___' + str(datetime.now())
        res = super(BSStockPicking, self).write(vals)
        return res

class ResCountryState(models.Model):
    _inherit = "res.country.state"

    upload_enquiry_id = fields.Many2one('bs.enquiry')

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    @api.model
    def _format_aml_name(self, line_name, move_ref, move_name):
        ''' Format the display of an account.move.line record. As its very costly to fetch the account.move.line
        records, only line_name, move_ref, move_name are passed as parameters to deal with sql-queries more easily.

        :param line_name:   The name of the account.move.line record.
        :param move_ref:    The reference of the account.move record.
        :param move_name:   The name of the account.move record.
        :return:            The formatted name of the account.move.line record.
        '''
        
        names = []
        if move_name != '/':
            names.append(move_name)
        if move_ref and move_ref != '/':
            names.append(move_ref)
        if self._name != 'account.partner.ledger':
            if line_name and line_name != move_name and line_name != '/':
                names.append(line_name)
#         if self._name == 'account.partner.ledger':
#             inv = self.env['account.move'].sudo().search([('name','=',move_name),('move_type','=','out_invoice')])
#             if inv:
#                 names.append(inv.ref)
        name = '-'.join(names)
        return name
    
    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))
        ledger_type = self.env.context.get('ledger_type',False)
        templates = self._get_templates()
        report_manager = self._get_report_manager(options)

        render_values = {
            'report': {
                'name': self._get_report_name(),
                'summary': report_manager.summary,
                'company_name': self.env.company.name,
            },
            'options': options,
            'context': self.env.context,
            'model': self,
        }
        if additional_context:
            render_values.update(additional_context)

        # Create lines/headers.
        if line_id:
            headers = options['headers']
            lines = self._get_lines(options, line_id=line_id)
            template = templates['line_template']
        else:
            headers, lines = self._get_table(options)
            if ledger_type == 'bs':
                headers = [
                            [
                                {},
                                {'name': 'Date', 'class': 'date'},
                                {'name': 'JRNL'}, 
                                {'name': 'Account'},
                                {'name': 'Invoice/ Payment  Ref Number'},
                                {'name': 'Item Description'},
                                {'name': 'Total Qty'},
                                {'name': 'Customer Ref/ PO'},
                                {'name': 'Site Name'},
                                {'name': 'Delivery Location'},
                                {'name': 'Vehicle Number'},
                                {'name': 'Matching Number'},
                                {'name': 'Payment Terms'},
                                {'name': 'Amount Due', 'class': 'number'},
                                {'name': 'Due Date', 'class': 'date'},
                                {'name': 'Date of Payment', 'class': 'date'},
                                {'name': 'Delay Days'},  
                                {'name': 'Initial Balance', 'class': 'number'},
                                {'name': 'Debit', 'class': 'number'},
                                {'name': 'Credit', 'class': 'number'}, 
                                {'name': 'Closing Balance', 'class': 'number'}
                             ]
                        ]
            options['headers'] = headers
            template = templates['main_template']
        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)
        if ledger_type == 'bs':
            for line in lines:
                if "colspan" in line:
                    line['columns'] = [
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''}]+ line.get('columns')
        render_values['lines'] = {'columns_header': headers, 'lines': lines}

        # Manage footnotes.
        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        # Render.
        html = self.env.ref(template)._render(render_values)
        if self.env.context.get('print_mode', False):
            for k,v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html

    
    @api.model
    def download_xlsx(self, opt):
        partner = self.env.user.partner_id
        part = 'partner_'+str(partner.id)
        df = opt.get('date_from')
        if df:
            cdf = datetime.strptime(df, '%Y-%m-%d').strftime('%d/%m/%Y')
        if not df:
            starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)
            cdf = starting_day_of_current_year.strftime('%d/%m/%Y')
            df =  starting_day_of_current_year.strftime('%Y-%m-%d')
        dt = opt.get('date_to')
        if dt:
            cdt = datetime.strptime(dt, '%Y-%m-%d').strftime('%d/%m/%Y')
        if not dt:
            ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)
            cdt = ending_day_of_current_year.strftime('%d/%m/%Y')
            dt =  ending_day_of_current_year.strftime('%Y-%m-%d')
        strn = 'From '+str(cdf)+' to  '+str(cdt)
        options = {
            'ledger_type':'bs',
            'unfolded_lines': [part],
            'date': {
                'string': strn,
                'period_type': 'custom',
                'mode': 'range',
                'strict_range': False,
                'date_from': df,
                'date_to': dt,
                'filter': 'custom'},
            'account_type': [
                {'id': 'receivable', 'name': 'Receivable', 'selected': False},
                {'id': 'payable', 'name': 'Payable', 'selected': False}],
            'all_entries': False,
            'partner': True,
            'partner_ids': [partner.id],
            'partner_categories': [],
            'selected_partner_ids': [partner.name],
            'selected_partner_categories': [],
            'unfold_all': False,
            'unreconciled': False,
            'unposted_in_period': False,
            'headers': [
                [
                    {'name': 'Date', 'class': 'date'},
                    {'name': 'JRNL'}, 
                    {'name': 'Account'},
                    {'name': 'Invoice/ Payment  Ref Number'},
                    {'name': 'Item Description'},
                    {'name': 'Total Qty'},
                    {'name': 'Customer Ref/ PO'},
                    {'name': 'Site Name'},
                    {'name': 'Delivery Location'},
                    {'name': 'Vehicle Number'},
                    {'name': 'Matching Number'},
                    {'name': 'Payment Terms'},
                    {'name': 'Amount Due', 'class': 'number'},
                    {'name': 'Due Date', 'class': 'date'},
                    {'name': 'Date of Payment', 'class': 'date'},
                    {'name': 'Delay Days'},  
                    {'name': 'Initial Balance', 'class': 'number'},
                    {'name': 'Debit', 'class': 'number'},
                    {'name': 'Credit', 'class': 'number'}, 
                    {'name': 'Closing Balance', 'class': 'number'}
                 ]
            ]
        }
        x =  self.with_context({'model': 'account.partner.ledger'}).print_xlsx(options)
        return x

    @api.model
    def download_pdf(self, opt):
        partner_id = self.env.user.partner_id.id
        open_part = 'partner_'+str(partner_id)
        df = opt.get('date_from')
        if df:
            cdf = datetime.strptime(df, '%Y-%m-%d').strftime('%d/%m/%Y')
        if not df:
            starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)
            cdf = starting_day_of_current_year.strftime('%d/%m/%Y')
            df =  starting_day_of_current_year.strftime('%Y-%m-%d')
        dt = opt.get('date_to')
        if dt:
            cdt = datetime.strptime(dt, '%Y-%m-%d').strftime('%d/%m/%Y')
        if not dt:
            ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)
            cdt = ending_day_of_current_year.strftime('%d/%m/%Y')
            dt =  ending_day_of_current_year.strftime('%Y-%m-%d')
        strn = 'From '+str(cdf)+' to  '+str(cdt)
        options = {
            'unfolded_lines': [open_part],
            'date': {
                'string': strn,
                'period_type': 'custom',
                'mode': 'range',
                'strict_range': False,
                'date_from': df,
                'date_to': dt,
                'filter': 'custom'},
            'account_type': [
                {'id': 'receivable', 'name': 'Receivable', 'selected': False},
                {'id': 'payable', 'name': 'Payable', 'selected': False}],
            'all_entries': True,
            'partner': True,
            'partner_ids': [partner_id],
            'partner_categories': [],
            'selected_partner_ids': ['Administrator'],
            'selected_partner_categories': [],
            'unfold_all': False,
            'unreconciled': False,
            'unposted_in_period': False,
            'headers': [[{}, {'name': 'JRNL'}, {'name': 'Account'}, {'name': 'Ref'}, {'name': 'Due Date', 'class': 'date'}, {'name': 'Matching Number'}, {'name': 'Initial Balance', 'class': 'number'}, {'name': 'Debit', 'class': 'number'}, {'name': 'Credit', 'class': 'number'}, {'name': 'Balance', 'class': 'number'}]]}
        x =  self.with_context({'model': 'account.partner.ledger'}).print_pdf(options)
        return x
    
    def bs_partner_ledger_get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        _logger.error("1 report ")
        sheet = workbook.add_worksheet(self._get_report_name()[:31])
        date_default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2,'font_size': 12})
        level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

        #Set the first column width to 50
        sheet.set_column(0, 0, 20)
        sheet.set_row(0, 50)
        sheet.set_column(1, 1, 30)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 70)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 20)
        sheet.set_column(12, 12, 20)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 20)
        sheet.set_column(15, 15, 20)
        sheet.set_column(16, 16, 20)
        sheet.set_column(17, 17, 20)
        sheet.set_column(18, 18, 20)
        sheet.set_column(19, 19, 20)

        y_offset = 0
        headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)
        x_offset = 0
        #company details
        _logger.error("2 report ")
        comp_offset = 3
        partner = self.env['res.partner'].sudo().browse(options.get('partner_ids')[0])
#         sheet.write(y_offset, x_offset, 'logo.png')
#         image_data = io.BytesIO(partner.company_id.logo.read())
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _logger.error("% report ",base_url)
        url = base_url+'/builderbay/static/src/images/logo.png'
        _logger.error("3 report ")
        image_data = io.BytesIO(urlopen(url).read())
        _logger.error("4 report ")
        sheet.insert_image(y_offset, x_offset, url, {'image_data': image_data})
        sheet.write(y_offset, comp_offset, partner.company_id.name,title_style)
        y_offset+=1
        sheet.write(y_offset, comp_offset, partner.company_id.street)
        y_offset+=1
        sheet.write(y_offset, comp_offset, partner.company_id.street2)
        sheet.write(y_offset, x_offset,'Partner Ledger')
        comaddr = ','.join([partner.company_id.city,partner.company_id.state_id.name])
        y_offset+=1
        sheet.write(y_offset, comp_offset, comaddr)
        sheet.write(y_offset, x_offset,'Customer Code:')
        comp_contry_pin = ','.join([partner.company_id.country_id.name,partner.company_id.zip])
        y_offset+=1
        sheet.write(y_offset, comp_offset, comp_contry_pin)
        y_offset+=1
        sheet.write(y_offset, x_offset,'Customer Name:')
        sheet.write(y_offset, x_offset+1,partner.name)
        sheet.write(y_offset, comp_offset, 'CIN:')
        sheet.write(y_offset, comp_offset+1, partner.company_id.company_registry)
        y_offset+=1
        sheet.write(y_offset, x_offset,'GSTIN:')
        sheet.write(y_offset, x_offset+1,partner.name)
        sheet.write(y_offset, comp_offset, 'GSTIN:')
        sheet.write(y_offset, comp_offset+1, partner.company_id.vat)
        y_offset+=1
        sheet.write(y_offset, x_offset,'Address:')
        sheet.write(y_offset, x_offset+1,partner.street)
        sheet.write(y_offset, comp_offset, 'PAN:')
        sheet.write(y_offset, comp_offset+1,'')
        y_offset+=1
        sheet.write(y_offset, x_offset+1,partner.street2)
        sheet.write(y_offset, comp_offset, 'Sales Person:')
        sheet.write(y_offset, comp_offset+1,'')
        y_offset+=1
        addr = ''
        if partner.city and partner.district_id and partner.state_id:
            addr = ','.join([partner.city,partner.district_id.name,partner.state_id.name])
        sheet.write(y_offset, x_offset+1,addr)
        sheet.write(y_offset, comp_offset, 'Sales Category:')
        sheet.write(y_offset, comp_offset+1,'')
        y_offset+=1
        contry_pin = ''
        if partner.country_id and partner.zip:
            contry_pin = ','.join([partner.country_id.name,partner.zip])
        sheet.write(y_offset, x_offset+1,contry_pin)
        sheet.write(y_offset, comp_offset, 'Email:')
        sheet.write(y_offset, comp_offset+1,partner.company_id.email)
        y_offset+=1
        sheet.write(y_offset, comp_offset, 'Customer Care:')
        sheet.write(y_offset, comp_offset+1,partner.company_id.phone)
        y_offset += 3
        # Add headers.
        headers = options.get('headers')
        for header in headers:
            for column in header:
                column_name_formated = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                colspan = column.get('colspan', 1)
                if colspan == 1:
                    sheet.write(y_offset, x_offset, column_name_formated, title_style)
                else:
                    sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan - 1, column_name_formated, title_style)
                x_offset += colspan
            y_offset += 1

        # Add lines.
        for y in range(0, len(lines)):
            if y:
                level = lines[y].get('level')
                if lines[y].get('caret_options'):
                    style = level_3_style
                    col1_style = level_3_col1_style
                elif level == 0:
                    y_offset += 1
                    style = level_0_style
                    col1_style = style
                elif level == 1:
                    style = level_1_style
                    col1_style = style
                elif level == 2:
                    style = level_2_style
                    col1_style = 'total' in lines[y].get('class', '').split(' ') and level_2_col1_total_style or level_2_col1_style
                elif level == 3:
                    style = level_3_style
                    col1_style = 'total' in lines[y].get('class', '').split(' ') and level_3_col1_total_style or level_3_col1_style
                else:
                    style = default_style
                    col1_style = default_col1_style
    
                #write the first column, with a specific style to manage the indentation
                cell_type, cell_value = self._get_cell_type_value(lines[y])
                if cell_value == 'Total':
                    lines[y]['colspan'] = 16
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
                else:
                    sheet.write(y + y_offset, 0, cell_value, col1_style)
    
                #write all the remaining cells
                for x in range(1, len(lines[y]['columns']) + 1):
                    cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                    if cell_type == 'date':
                        sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, date_default_style)
                    else:
                        sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return generated_file


class BSSORejectionReason(models.Model):
    _name = "bs.rejection.reason"

    name = fields.Char(string="Reason")

class BSPaymentTransaction(models.Model):
    _inherit = "payment.transaction"
    
    utr_no = fields.Char('UTR Number', copy=False)
    to_skip = fields.Boolean('Skip',copy=False, help="To Skip if already validated in requery api of atom", default=False)
#     state = fields.Selection(selection_add=[('failed', 'Failed')])
    
    #call back method
    def atom_callback(self, data):
        reference, status = data.get('MerchantTxnID'), data.get('VERIFIED')
        tx = self.env['payment.transaction'].search([('reference', '=', reference)])
        if status == 'SUCCESS':
            if tx: 
                tx._set_transaction_done()
                return True
        if status == 'FAILED':
            if tx: 
                tx._set_transaction_cancel()
                return False
        return False

class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    is_neft = fields.Boolean(string='Is NEFT/RTGS ?')
    customer_type = fields.Selection([('b2b', 'B2B'),
                                      ('b2c', 'B2C'),
                                      ('both', 'Both')], string='Customer Type', default="both")


class BSWebsite(models.Model):
    _inherit = "website"

    def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        print('line 11111',request.session)
        """ Return the current sales order after mofications specified by params.
        :param bool force_create: Create sales order if not already existing
        :param str code: Code to force a pricelist (promo code)
                         If empty, it's a special case to reset the pricelist with the first available else the default.
        :param bool update_pricelist: Force to recompute all the lines from sales order to adapt the price with the current pricelist.
        :param int force_pricelist: pricelist_id - if set,  we change the pricelist with this one
        :returns: browse record for the current sales order
        """
        self.ensure_one()
        partner = self.env.user.partner_id
        sale_order_id = request.session.get('sale_order_id')
        if not sale_order_id and not self.env.user._is_public():
            last_order = partner.last_website_so_id
            if last_order:
                available_pricelists = self.get_pricelist_available()
                # Do not reload the cart of this user last visit if the cart uses a pricelist no longer available.
                sale_order_id = last_order.pricelist_id in available_pricelists and last_order.id

        # Test validity of the sale_order_id
        sale_order = self.env['sale.order'].with_company(request.website.company_id.id).sudo().browse(sale_order_id).exists() if sale_order_id else None

        if not (sale_order or force_create or code):
            if request.session.get('sale_order_id'):
                request.session['sale_order_id'] = None
            return self.env['sale.order']

        if self.env['product.pricelist'].browse(force_pricelist).exists():
            pricelist_id = force_pricelist
            request.session['website_sale_current_pl'] = pricelist_id
            update_pricelist = True
        else:
            pricelist_id = request.session.get('website_sale_current_pl') or self.get_current_pricelist().id

        if not self._context.get('pricelist'):
            self = self.with_context(pricelist=pricelist_id)

        # cart creation was requested (either explicitly or to configure a promo code)
        if not sale_order:
            # TODO cache partner_id session
            pricelist = self.env['product.pricelist'].browse(pricelist_id).sudo()
            so_data = self._prepare_sale_order_values(partner, pricelist)
            sale_order = self.env['sale.order'].with_company(request.website.company_id.id).with_user(SUPERUSER_ID).create(so_data)

            # set fiscal position
            if request.website.partner_id.id != partner.id:
                sale_order.onchange_partner_shipping_id()
            else: # For public user, fiscal position based on geolocation
                country_code = request.session['geoip'].get('country_code')
                if country_code:
                    country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1).id
                    sale_order.fiscal_position_id = request.env['account.fiscal.position'].sudo().with_company(request.website.company_id.id)._get_fpos_by_region(country_id)
                else:
                    # if no geolocation, use the public user fp
                    sale_order.onchange_partner_shipping_id()

            request.session['sale_order_id'] = sale_order.id

        # case when user emptied the cart
        if not request.session.get('sale_order_id'):
            request.session['sale_order_id'] = sale_order.id

        # check for change of pricelist with a coupon
        pricelist_id = pricelist_id or partner.property_product_pricelist.id

        # check for change of partner_id ie after signup
        if sale_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
            flag_pricelist = False
            if pricelist_id != sale_order.pricelist_id.id:
                flag_pricelist = True
            fiscal_position = sale_order.fiscal_position_id.id

            # change the partner, and trigger the onchange
            sale_order.write({'partner_id': partner.id})
            sale_order.with_context(not_self_saleperson=True).onchange_partner_id()
            sale_order.write({'partner_invoice_id': partner.id})
            sale_order.onchange_partner_shipping_id() # fiscal position
            sale_order['payment_term_id'] = self.sale_get_payment_term(partner)

            # check the pricelist : update it if the pricelist is not the 'forced' one
            values = {}
            if sale_order.pricelist_id:
                if sale_order.pricelist_id.id != pricelist_id:
                    values['pricelist_id'] = pricelist_id
                    update_pricelist = True

            # if fiscal position, update the order lines taxes
            if sale_order.fiscal_position_id:
                sale_order._compute_tax_id()

            # if values, then make the SO update
            if values:
                sale_order.write(values)

            # check if the fiscal position has changed with the partner_id update
            recent_fiscal_position = sale_order.fiscal_position_id.id
            # when buying a free product with public user and trying to log in, SO state is not draft
            if (flag_pricelist or recent_fiscal_position != fiscal_position) and sale_order.state == 'draft':
                update_pricelist = True

        if code and code != sale_order.pricelist_id.code:
            code_pricelist = self.env['product.pricelist'].sudo().search([('code', '=', code)], limit=1)
            if code_pricelist:
                pricelist_id = code_pricelist.id
                update_pricelist = True
        elif code is not None and sale_order.pricelist_id.code and code != sale_order.pricelist_id.code:
            # code is not None when user removes code and click on "Apply"
            pricelist_id = partner.property_product_pricelist.id
            update_pricelist = True

        # update the pricelist
        if update_pricelist:
            request.session['website_sale_current_pl'] = pricelist_id
            values = {'pricelist_id': pricelist_id}
            sale_order.write(values)
            for line in sale_order.order_line:
                if line.exists():
                    sale_order._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=0)

        return sale_order

class BSARNumber(models.Model):
    _name = 'bs.arn'

    month = fields.Selection([('1', 'January'),
                            ('2', 'February'),
                            ('3', 'March'),
                            ('4', 'April'),
                            ('5', 'May'),
                            ('6', 'June'),
                            ('7', 'July'),
                            ('8', 'August'),
                            ('9', 'September'),
                            ('10', 'October'),
                            ('11', 'November'),
                            ('12', 'December')], string="Month")
    year = fields.Char(default=datetime.now().year, string="Year")
    arn_no = fields.Char('ARN Number')
    filed_status = fields.Selection([('yes','Yes'),('no','No')], string="GST Filed Status")
    filing_date = fields.Date('ARN Filing Date')

    _sql_constraints = [
        ('arn_uniq', 'unique (month,year)', 'The GST filing should be unique per month !')
    ]

    @api.onchange('arn_no')
    def _onchange_arn_no(self):
        if self.arn_no and self.filed_status == 'yes':
            CurrMonthInvs = self.env['account.move'].search([]).filtered(lambda x: x.invoice_date and
            str(x.invoice_date.month) == self.month and x.state == 'posted')
            if CurrMonthInvs: CurrMonthInvs.write({'arn_id': self._origin.id})
            
            
class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    def _get_columns_name(self, options):
        columns = [
            {'name': _('Date'), 'class': 'date'},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Ref')},
            {'name': _('Due Date'), 'class': 'date'},
            {'name': _('Matching Number')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})
        columns.append({'name': _('Balance'), 'class': 'number'})
        return columns

    #Overridden
    @api.model
    def _get_query_amls(self, options, expanded_partner=None, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_partner:    The res.partner record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_partner:
            domain = [('partner_id', '=', expanded_partner.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('partner_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._get_options_sum_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        query = '''
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                account_move_line.name,
                account_move_line.ref,
                account_move_line.company_id,
                account_move_line.account_id,
                account_move_line.payment_id,
                account_move_line.partner_id,
                account_move_line.currency_id,
                account_move_line.amount_currency,
                account_move_line.matching_number,
                ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                account_move_line__move_id.name         AS move_name,
                company.currency_id                     AS company_currency_id,
                partner.name                            AS partner_name,
                account_move_line__move_id.move_type         AS move_type,
                account.code                            AS account_code,
                account.name                            AS account_name,
                journal.code                            AS journal_code,
                journal.name                            AS journal_name
            FROM account_move_line
            LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
            WHERE %s 
            ORDER BY account_move_line.date,account_move_line.id
        ''' % (ct_query, where_clause)

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    # extended
    @api.model
    def _get_report_line_partner(self, options, partner, initial_balance, debit, credit, balance):
        company_currency = self.env.company.currency_id
        unfold_all = self._context.get('print_mode') and not options.get('unfolded_lines')
        columns = [
            {'name': self.format_value(initial_balance), 'class': 'number'},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
        ]
#         ledger_type = self._context.get('ledger_type',False)
#         if ledger_type == 'bs':
#             item_desc = ''
#             total_qty = ''
#             cus_ref = ''
#             site_name = ''
#             del_loc = ''
#             vehicl_numb = ''
#             pay_trm = ''
#             amt_due = 0.0
#             date_payment = ''
#             delay_days = ''
#               
#             columns = [
#                 {'name': ''},
#                 {'name': ''},
#                 {'name': ''},
#                 {'name': item_desc},
#                 {'name': total_qty},
#                 {'name': cus_ref},
#                 {'name': site_name},
#                 {'name': del_loc},
#                 {'name': vehicl_numb},
#                 {'name': ''},
#                 {'name': pay_trm},
#                 {'name': amt_due, 'class': 'number'},
#                 {'name': '', 'class': 'date'},
#                 {'name': date_payment, 'class': 'date'},
#                 {'name': delay_days},  
#                 {'name': self.format_value(initial_balance), 'class': 'number'},
#                 {'name': self.format_value(debit), 'class': 'number'},
#                 {'name': self.format_value(credit), 'class': 'number'},
#                 {'name': self.format_value(initial_balance), 'class': 'number'},
#             ]

        
        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': ''})
        columns.append({'name': self.format_value(balance), 'class': 'number'})

        return {
            'id': 'partner_%s' % partner.id,
            'partner_id': partner.id,
            'name': (partner.name or '')[:128],
            'columns': columns,
            'level': 2,
            'trust': partner.trust,
            'unfoldable': not company_currency.is_zero(debit) or not company_currency.is_zero(credit),
            'unfolded': 'partner_%s' % partner.id in options['unfolded_lines'] or unfold_all,
            'colspan': 6,
        }

    # overridden
    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        ledger_type = options.get('ledger_type', False)
        if ledger_type == 'bs':
            if aml['payment_id']:
                caret_type = 'account.payment'
            else:
                caret_type = 'account.move'
            item_desc = ''
            total_qty = ''
            cus_ref = ''
            site_name = ''
            del_loc = ''
            vehicl_numb = ''
            pay_trm = ''
            amt_due = 0.0
            date_payment = ''
            delay_days = ''
            if caret_type == 'account.move':
                account_move = self.env['account.move'].sudo().browse(int(aml['id']))
                if account_move.partner_shipping_id:
                    del_loc = ','.join([account_move.partner_shipping_id.street,account_move.partner_shipping_id.street2,account_move.partner_shipping_id.city])
                amt_due = account_move.amount_residual
                total_qty = sum(account_move.invoice_line_ids.mapped('quantity'))
                item_desc = account_move.invoice_line_ids.mapped('product_id').mapped('product_tmpl_id').name
                so = self.env['sale.order'].sudo().search([('name','=',account_move.invoice_origin)])
                if so: pay_trm = so.payment_term_id.name
                delay_days = account_move.invoice_date_due
                date_payment = account_move.invoice_payments_widget
            date_maturity = aml['date_maturity'] and format_date(self.env,
                                                                 fields.Date.from_string(aml['date_maturity']))
            columns = [
                {'name': aml['journal_code']},
                {'name': aml['account_code']},
                {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name'])},
                {'name': item_desc},
                {'name': total_qty},
                {'name': cus_ref},
                {'name': site_name},
                {'name': del_loc},
                {'name': vehicl_numb},
                {'name': aml['matching_number'] or ''},
                {'name': pay_trm},
                {'name': amt_due, 'class': 'number'},
                {'name': date_maturity or '', 'class': 'date'},
                {'name': date_payment, 'class': 'date'},
                {'name': delay_days},
                {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
                {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
                {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
            ]
            if self.user_has_groups('base.group_multi_currency'):
                if aml['currency_id']:
                    currency = self.env['res.currency'].browse(aml['currency_id'])
                    formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
                    columns.append({'name': formatted_amount, 'class': 'number'})
                else:
                    columns.append({'name': ''})
            columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
            return {
                'id': aml['id'],
                'parent_id': 'partner_%s' % partner.id,
                'name': format_date(self.env, aml['date']),
                'class': 'text',  # do not format as date to prevent text centering
                'columns': columns,
                'caret_options': caret_type,
                'level': 2,
            }


        if aml['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move'

        
        date_maturity = aml['date_maturity'] and format_date(self.env, fields.Date.from_string(aml['date_maturity']))
        date_maturity = datetime.strptime(date_maturity, '%d/%m/%Y').strftime('%d-%B-%Y') if date_maturity else ''
        # print('date_maturity',date_maturity, datetime.datetime.strptime(date_maturity,'%d/%m/%Y'))
        payment = self.env['account.payment'].browse(int(aml['payment_id'])) if aml['payment_id'] else False
        if payment:
            if payment.journal_id.type in ('bank','cash'):
                date_maturity = ''
        columns = [
            {'name': aml['journal_code']},
            {'name': aml['account_code']},
            {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name'])},
            {'name': date_maturity, 'class': 'date'},
            {'name': aml['matching_number'] or ''},
            {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            if aml['currency_id']:
                currency = self.env['res.currency'].browse(aml['currency_id'])
                formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
                columns.append({'name': formatted_amount, 'class': 'number'})
            else:
                columns.append({'name': ''})
        columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
        return {
            'id': aml['id'],
            'parent_id': 'partner_%s' % partner.id,
            'name': datetime.strptime(format_date(self.env, aml['date']), '%d/%m/%Y').strftime('%d-%B-%Y')
            if format_date(self.env, aml['date']) else '',
            'class': 'text',  # do not format as date to prevent text centering
            'columns': columns,
            'caret_options': caret_type,
            'level': 2,
        }


class BSPurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _order = 'id desc, priority desc, date_order desc'

    t_and_c = fields.One2many('bs.select.terms.conditions', 'po_id', string="Terms & Conditions")
    delivery_address = fields.Text('Delivery Address')

    def get_num2words(self, Amount):
        AmountString = ''
        if Amount:
            AmountString = BSnum2words.num2words("%.2f"%(Amount)) + ' Only'
        return AmountString

    @api.onchange('origin')
    def _onchange_so_ref(self):
        if self.origin:
            SO = self.env['sale.order'].sudo().search([('name','=',self.origin)], limit=1)
            if SO and SO.partner_shipping_id:
                ShipAdd = SO.partner_shipping_id
                DelAdd = ShipAdd.name if not ShipAdd.parent_id else ShipAdd.parent_id.name
                if ShipAdd.street: DelAdd += '\n' + ShipAdd.street
                if ShipAdd.street2: DelAdd += '\n' + ShipAdd.street2
                if ShipAdd.district_id: DelAdd += '\n' + ShipAdd.district_id.name
                if ShipAdd.city: DelAdd += ', '+ShipAdd.city
                if ShipAdd.state_id: DelAdd += '\n' + ShipAdd.state_id.name + ' (' + ShipAdd.state_id.code + ')'
                if ShipAdd.zip: DelAdd += ' - '+ ShipAdd.zip
                self.delivery_address = DelAdd
        else:
            self.delivery_address = ""

    def get_so_del_address(self, Origin):
        return self.env['sale.order'].sudo().search([('name','=',Origin)], limit=1)

class BSServiceability(models.Model):
    _name = "bs.pincode.serviceability"
    _order = 'pincode desc'

    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state', 'State')
    district_id = fields.Many2one('bs.district', 'District')
    pincode = fields.Char('Pincode')
    is_serviceable = fields.Boolean('Is Serviceable', default=False)

class BSTermsConditions(models.Model):
    _name = "bs.terms.conditions"

    category = fields.Selection([('steel', 'Steel'),
                                 ('cement', 'Cement'),
                                 ('paints', 'Paints'),
                                 ('blocks', 'Blocks'),
                                 ('rmc', 'RMC'),
                                 ('safety', 'Safety Products'),
                                 ('bricks', 'Bricks')], string="Category")
    name = fields.Text(string="Terms")


class BSSelectTandC(models.Model):
    _name = "bs.select.terms.conditions"

    sequence = fields.Integer('Sequence', help="Sequence used to order T&C for report")
    is_selected = fields.Boolean(string="Select")
    tandc_id = fields.Many2one("bs.terms.conditions", 'Terms')
    sale_id = fields.Many2one('sale.order')
    move_id = fields.Many2one('account.move')
    po_id = fields.Many2one('purchase.order')
    category = fields.Selection([('steel', 'Steel'),
                                 ('cement', 'Cement'),
                                 ('paints', 'Paints'),
                                 ('blocks', 'Blocks'),
                                 ('rmc', 'RMC'),
                                 ('safety', 'Safety Products'),
                                 ('bricks', 'Bricks')], string="Category") #Ensure as per bs.terms.conditions category

    @api.onchange('category')
    def _onchange_category(self):
        if self.category:
            return {'domain':{'tandc_id':[('category','=',self.category)]}}

class BSHomepageSellers(models.Model):
    _name = "bs.homepage.sellers"
    _rec_name = "partner_id"
    _order = "sequence"

    partner_id = fields.Many2one('res.partner')
    sequence = fields.Integer('Sequence')
    seller_id = fields.Many2one('bs.homepage')
    image = fields.Image("Image", max_width=128, max_height=128)
    
    
 #### delivery receiver verifiaction ####   
class BSDverify(models.Model):
    _name = 'bs.delivery.verification'

    name = fields.Char('Receiver Person Name')
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    comments = fields.Char('Comments')
    otp = fields.Char('otp')
    is_link_send = fields.Boolean(string="Link Sent")
    email_token = fields.Char(string="Token")
    company_id = fields.Many2one('res.company')
    sale_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner')
    user_id = fields.Many2one('res.users')
    delivry_person = fields.Char('Delivery person Name')
    delivry_person_contact = fields.Char('Delivery person Contact')
    site_name = fields.Char('Site Name')
    site_location = fields.Char('Site Location')
    landmark = fields.Char('Landmark')
    
    def send_verification_email(self, emails):
        import hmac
        import hashlib
        base_url = self.env['ir.config_parameter'].sudo().get_param('base.url')
        base_link =  'http://localhost:8069/bs/verified'
        params = {'email':self.email,'mobile':self.mobile}
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        token = '%s?%s' % (base_link, ' '.join('%s=%s' % (key, params[key]) for key in sorted(params)))
        hm = hmac.new(secret.encode('utf-8'), token.encode('utf-8'), hashlib.sha1).hexdigest()
        email_url =  'http://localhost:8069/bs/verified?code='+str(self.id)+'&string='+hm
        subject = _("Delivery Verification Confirmation")
        body = _("""Please click on below link to confirm:
               <a href="%(url)s">%(link)s </a>.
            """,link=hm ,url=email_url)
        email = self.env['ir.mail_server'].build_email(
                    email_from=self.env.user.company_id.email,
                    email_to=emails,
                    subject=subject, body=body,subtype='html',
                )
        self.env['ir.mail_server'].send_email(email)
        self.is_link_send = True
        self.email_token = hm
        return True
    
    def send_info_email(self, emails):
        subject = _("Delivery Confirmation")
        body = _("""
            Dear %s,
            Your order %s delivered at site location:%s, site name:%s .
            Received by %s / %s  .
            If found any suspicious for this order please call us immediately %s
            """% (self.partner_id.name, self.sale_id.name, self.site_location,self.site_name, self.name, self.mobile, '96424 96424') )
        email = self.env['ir.mail_server'].build_email(
                    email_from=self.env.user.company_id.email,
                    email_to=emails,
                    subject=subject, body=body,
                )
        self.env['ir.mail_server'].send_email(email)
        return True
    
    def get_default_value(self, user, picking):
        picking = self.env['stock.picking'].sudo().search([('delivery_person','=',user.id),('id','=',picking)])
        sale_order = picking.sale_id
        vals = {
            'so_name':sale_order.name,
            'sale_id':sale_order.id,
            'partner_id':sale_order.partner_id.id,
            'partner_name':sale_order.partner_id.name,
            'user_id':user,
            'bs_user_id':user.id,
            'delivry_person':user.name,
            'site_name':sale_order.partner_id.site_name,
            'site_location':sale_order.partner_id.site_location
            }
        return vals
    
    def get_default_assign_value(self, user):
        pickings = self.env['stock.picking'].sudo().search([('delivery_person','=',user.id)])
        list_vals = []
        for picking in pickings:
            sale_order = picking.sale_id
            vals = {
                'so_name':sale_order.name,
                'sale_id':sale_order.id,
                'partner_id':sale_order.partner_id.id,
                'partner_name':sale_order.partner_id.name,
                'user_id':user,
                'bs_user_id':user.id,
                'delivry_person':user.name,
                'site_name':sale_order.partner_id.site_name,
                'site_location':sale_order.partner_id.site_location,
                'picking_id':picking.id
                }
            list_vals.append(vals)
        return list_vals
    

class BSHomepageBackend(models.Model):
    _name = "bs.homepage"
    _rec_name = 'website_id'

    footer_link_ids = fields.One2many('bs.footer.links', 'footer_link_id', string='Footer Links')
    header_search_ids = fields.One2many('bs.header.search', 'header_search_id', string="Header Search")

    company_id = fields.Many2one('res.company', 'Company')
    website_id = fields.Many2one('website', string='Website')

    #homepage
    banner_ids = fields.One2many('banner.image', 'banner_id', string='Banners')
    client_review_ids = fields.One2many('bs.client.review', 'review_id', string="Client Reviews")
    our_seller_ids = fields.One2many('bs.homepage.sellers', 'seller_id', string="Our Sellers")
    our_brand_ids = fields.One2many('bs.homepage.brands', 'our_brand_id', string="Our Brands")

    hot_deals_label = fields.Char('Hot Deals Label')
    hot_deal_ids = fields.One2many('bs.homepage.products', 'hot_deal_id', string="Hot Deals")

    best_selling_label = fields.Char('Best Selling Label')
    best_selling_ids = fields.One2many('bs.homepage.products', 'best_selling_id', string="Best Selling Products")

    trending_product_label = fields.Char('Trending Products Label')
    trending_product_ids = fields.One2many('bs.homepage.products', 'trending_prod_id', string="Trending Products of Week")

    top_blocks_label = fields.Char('Top Blocks Label')
    top_block_ids = fields.One2many('bs.homepage.products', 'top_block_id', string="Top Selling Blocks")

    cement_brand_label = fields.Char('Cement Brands Label')
    cement_brand_ids = fields.One2many('bs.homepage.brands', 'cement_brand_id', string="Top Cement Brands")

    safety_brand_label = fields.Char('Safety Brands Label')
    safety_brand_ids = fields.One2many('bs.homepage.brands', 'safety_brand_id', string="Top Safety Brands")

    steel_brand_label = fields.Char('Steel Brands Label')
    steel_brand_ids = fields.One2many('bs.homepage.brands', 'steel_brand_id', string="Top Steel Brands")

    block_brand_label = fields.Char('Block Brands Label')
    block_brand_ids = fields.One2many('bs.homepage.brands', 'block_brand_id', string="Top Blocks Brands")

    top_category_ids = fields.One2many('bs.homepage.categories', 'top_categ_id', string="Top Categories")

    safety_category_label = fields.Char('Safety Categories Label')
    safety_category_ids = fields.One2many('bs.homepage.categories', 'safety_categ_id', string="Top Safety Categories")
    
    
    
    def get_cdn_url(self, brand):
        final_uri_preview = "/web/static/src/img/placeholder.png"
        try:
            from werkzeug import urls
            import requests
            s3 = ['brand']
            
            Website_env = self.env['website']
            website = Website_env.get_current_website()
            cdn_url = website.cdn_url
            if cdn_url:
                s3.append(slug(brand))
                uri = '/'.join(s3)
                final_uri = urls.url_join(cdn_url, uri)
                response = requests.get(final_uri)
                if response.status_code != 200:
                    homepage = self.env['bs.homepage'].search([],limit=1)
                    return final_uri_preview
                return final_uri
            else:
                return final_uri_preview
        except:
            pass
        return final_uri_preview


class BSHomepageBrands(models.Model):
    _name = "bs.homepage.brands"
    _rec_name = "brand_id"
    _order = "sequence"

    label = fields.Char('Label')
    brand_id = fields.Many2one('product.attribute.value')
    sequence = fields.Integer('Sequence')
    our_brand_id = fields.Many2one('bs.homepage')
    # company_id1 = fields.Many2one('bs.homepage')
    cement_brand_id = fields.Many2one('bs.homepage')
    safety_brand_id = fields.Many2one('bs.homepage')
    steel_brand_id = fields.Many2one('bs.homepage')
    block_brand_id = fields.Many2one('bs.homepage')
    image = fields.Image("Image")
    s3_url = fields.Char('S3 Bucket URL', help="To get image from s3 bucket")


class BSHomepageProducts(models.Model):
    _name = "bs.homepage.products"
    _rec_name = "product_id"
    _order = "sequence"

    label = fields.Char('Label')
    product_id = fields.Many2one('product.template')
    sequence = fields.Integer('Sequence')
    # company_id = fields.Many2one('bs.homepage')
    hot_deal_id = fields.Many2one('bs.homepage')
    best_selling_id = fields.Many2one('bs.homepage')
    trending_prod_id = fields.Many2one('bs.homepage')
    top_block_id = fields.Many2one('bs.homepage')
    image = fields.Image("Image", max_width=128, max_height=128)
    s3_url = fields.Char('S3 Bucket URL', help="To get image from s3 bucket")

class BSHomepageCategories(models.Model):
    _name = "bs.homepage.categories"
    _rec_name = "category_id"
    _order = "sequence"

    label = fields.Char('Label')
    category_id = fields.Many2one('product.public.category')
    sequence = fields.Integer('Sequence')
    # company_id = fields.Many2one('bs.homepage')
    top_categ_id = fields.Many2one('bs.homepage')
    safety_categ_id = fields.Many2one('bs.homepage')
    image = fields.Image("Image", max_width=128, max_height=128)
    s3_url = fields.Char('S3 Bucket URL', help="To get image from s3 bucket")
 
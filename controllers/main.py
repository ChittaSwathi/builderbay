from odoo import http, _
from odoo.http import request
import requests
import json
import datetime
from datetime import datetime
import re
from odoo.addons.web.controllers.main import ReportController
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval, time
from odoo.http import content_disposition, request
from odoo.exceptions import ValidationError, UserError, RedirectWarning


class BSReportController(ReportController):

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token, context=None):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        try:
            if type in ['qweb-pdf', 'qweb-text']:
                converter = 'pdf' if type == 'qweb-pdf' else 'text'
                extension = 'pdf' if type == 'qweb-pdf' else 'txt'

                pattern = '/report/pdf/' if type == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')
                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids, converter=converter, context=context)
                else:
                    # Particular report:
                    data = dict(url_decode(url.split('?')[1]).items())  # decoding the args represented in JSON
                    if 'context' in data:
                        context, data_context = json.loads(context or '{}'), json.loads(data.pop('context'))
                        context = json.dumps({**context, **data_context})
                    response = self.report_routes(reportname, converter=converter, context=context, **data)

                report = request.env['ir.actions.report']._get_report_from_name(reportname)
                filename = "%s.%s" % (report.name, extension)

                if docids:
                    ids = [int(x) for x in docids.split(",")]
                    obj = request.env[report.model].browse(ids)

                    if report.model == 'account.move' and not obj.authorized_by:
                        ReportType = 'Invoice' if obj.move_type=='out_invoice' else 'Bill'
                        raise UserError(_('%s needs to be Verified to proceed further.'%(ReportType)))

                    if report.print_report_name and not len(obj) > 1:
                        report_name = safe_eval(report.print_report_name, {'object': obj, 'time': time})
                        filename = "%s.%s" % (report_name, extension)
                response.headers.add('Content-Disposition', content_disposition(filename))
                response.set_cookie('fileToken', token)
                return response
            else:
                return
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))


class BSCustomWebsite(http.Controller):

    @http.route('/notifications', type="http", auth="user", website=True, sitemap=True)
    def bs_notifications(self):
        Partner = request.env.user.partner_id
        Notifications = request.env['bs.notification'].sudo().search([('partner_id','=',Partner.id)])
        return request.render('builderbay.bs_notifications', {'notifications':Notifications})

    @http.route('/contactus', type="http", auth="public", website=True, sitemap=True) #Overridden
    def bs_contactus(self):
        return request.render('builderbay.bs_contactus')

    @http.route('/bs/contactus', type="json", auth="public", website=True, sitemap=False)
    def bs_contactus_submit(self, **kw):
        try:
            return request.env['crm.lead'].sudo().create(kw)
        except Exception as e:
            return False


    @http.route('/policy/privacy', type="http", auth="public", website=True)
    def bs_policies(self):
        return request.render('builderbay.bs_privacy_policy')

    @http.route('/faq', type="http", auth="public", website=True)
    def bs_faqs(self):
        return request.render('builderbay.coming_soon')

    @http.route('/get/variant', type='json', auth="public", sitemap=False, website=False)
    def bs_get_product_variant(self, **kw):
        AttrIDs = kw.get('attr_ids')
        if AttrIDs:
            ProdTmp = request.env['product.template'].sudo().browse(kw.get('product_tmpl_id'))
            ProductRec = request.env['product.product'].sudo().search([('public_categ_ids', 'child_of',
                                                           ProdTmp.public_categ_ids.ids)]). \
                filtered(
                lambda x: set(x.product_template_attribute_value_ids.mapped('product_attribute_value_id.id')) == set(
                    AttrIDs))

            if ProductRec:
                print('ProductRec.product_tmpl_id',ProductRec.product_tmpl_id)
                TemplateData = request.env['ir.ui.view']._render_template('builderbay.cement_box_tr',
                                                                          {'product':ProductRec.product_tmpl_id[0],
                                                                           'variant':ProductRec[0],
                                                                           'tr_style':'',
                                                                           'show_trash':True,
                                                                           'selected_qty': kw.get('selected_qty',0)})
                return TemplateData
        return ''

    @http.route('/signup/states', type='json', auth="public", sitemap=False, website=True)
    def bs_control_signup_states(self, DistrictID, **kw):
        if DistrictID:
            return request.env['bs.district'].sudo().search([('id','=',int(DistrictID))], limit=1).state_id.id
        return request.env['bs.district'].sudo().search([]).mapped('state_id.id')

    @http.route('/signup/districts', type='json', auth="public", sitemap=False, website=True)
    def bs_control_signup_districts(self, StateID, **kw):
        if StateID:
            return request.env['bs.district'].sudo().search([('state_id','=',int(StateID))]).mapped('id')
        return request.env['bs.district'].sudo().search([]).mapped('id')

    @http.route('/pincode/service', type='json', auth="public", sitemap=False, website=True)
    def bs_pincode_service(self, **kw):
        Pincode = kw.get('pincode')
        if Pincode:
            PincodeService = request.env['bs.pincode.serviceability'].sudo().search([('pincode','=',Pincode),
                                                                 ('is_serviceable', '=',True)],limit=1)
            if PincodeService: ReturnText, Class = "Delivery available at %s"%(Pincode), "text-success"
            else: ReturnText, Class = "Delivery not available at %s. Please raise a request, our customer executive will reach back to you."%(Pincode), "text-danger"
        else:
            ReturnText, Class = "Please enter pincode.", "text-danger"
        return ReturnText, Class

    @http.route('/todo', type="http", auth="public", website=True, sitemap=False)
    def todo_upload_info(self, **post):
        return request.render('builderbay.todo_upload_info')

    @http.route('/sell', type="http", auth="public", website=True)
    def sell_with_us(self, **post):
        return request.render('builderbay.coming_soon')

    # TODO: check &amp; implement
    @http.route('/pingback/sms', type="http", auth="public", website=True)
    def pingback_url_sms(self, **post):
        #print('3333333333333333333333', request.env.company.get_token, post)
        #return request.env.company.get_token
        return ""

    @http.route(['/brands',
                 '/brands/<string:alphabet>'], type = "http", auth = "public", website = True)
    def return_brands(self, alphabet='a', **post) :
        PartnerCustType = request.env.user.partner_id.customer_type if request.env.user else False
        Brands = request.env['product.attribute.value'].sudo().search([('name','=ilike',alphabet+'%'),
                                                                       ('customer_type','in',['both',PartnerCustType]),
                                                                       ('attribute_id','=',request.env.ref('builderbay.brand_attribute').id)])
        return request.render('builderbay.brands_page', {'brands': Brands, 'are_top_brands': False})


    @http.route(['/topbrands',
                 '/topbrands/<int:category>'], type = "http", auth = "public", website = True)
    def return_topbrands(self, category=False, **post) :
        PartnerCustType = request.env.user.partner_id.customer_type if request.env.user else False
        Brands = request.env['product.attribute.value'].sudo().search([('attribute_id','=',request.env.ref('builderbay.brand_attribute').id),
                                                                       ('customer_type', 'in',['both', PartnerCustType]),
                                                                       ('is_top_brand','=',True)])
        return request.render('builderbay.brands_page', {'brands': Brands, 'are_top_brands': True})


    # L1 category page
    # @http.route('/category/<int:CategId>/<string:CategName>', type = "http", auth = "public", website = True)
    # def return_categories(self, CategId, **post):
    #
    #     Partner = request.env.user.partner_id
    #     EcommCategObj = request.env['product.public.category'].sudo()
    #     CategRec = EcommCategObj.browse(CategId)
    #     values = {'sibling_categs': EcommCategObj.search([('parent_id', 'in', [CategRec.parent_id.id]
    #                                 if CategRec.parent_id else []),
    #                                 ('customer_type','in',[CategRec.parent_id.customer_type, 'both'])]),
    #               'child_categs': CategRec.child_id,
    #               'trending_categs' : EcommCategObj.search([('parent_id','child_of',CategRec.id),
    #                                                         ('is_trending','=',True)], limit=6),
    #               'ecomm_categ': CategRec,
    #               'all_brands': EcommCategObj.get_brands(eCommCategIDs=[CategId]),
    #               'featured_products': request.env['product.template'].sudo().search([('is_hot_deal', '=', True),
    #                                                           ('public_categ_ids', 'child_of',CategRec.id)]),
    #               'top_brands': request.env['product.public.category'].sudo().get_brands(eCommCategIDs=[CategRec.id]).filtered(lambda x: x.is_top_brand),
    #               }
    #     if (CategRec.l2_view and CategRec.l2_view == 'tile_view'):
    #         return request.render('builderbay.bs_l2_tile_view', values)
    #     elif (CategRec.l2_view and CategRec.l2_view == 'ecomm_view'):
    #         return request.render('builderbay.bs_ecommerce_template', values)
    #     else:
    #         return request.render('builderbay.bs_l2_page', values)


    @http.route('/change/address/shipping', type='json', auth="public", sitemap=False, website=True)
    def bs_change_shipping_add(self, **kw):
        if kw.get('partner_id') and kw.get('default_shipping_id'):
            request.env['res.partner'].sudo().browse(int(kw.get('partner_id'))).write(
                {'default_shipping_id': int(kw.get('default_shipping_id', 'partner_id'))})

    @http.route('/bs/gst/verify', type='json', auth="none", sitemap=False, website=True)
    def bs_gst_verify(self, **kw):
        '''
            GST API verifies the provided GSTIN and returns the response with all valid detailed respective to the same.
            To reduce charge per hit, we will store every GST input in our database, so that we can return the same if exists else hit the actual API
        '''
        Company = request.env['res.company'].sudo().search([],limit=1)
        GSTIN = str(kw.get('gstin','')).strip()
        APIKey = Company.gst_prod_key or Company.gst_pre_prod_key
        AgencyKey = Company.gst_agent_key
        URL = Company.gst_url

        if GSTIN and URL and AgencyKey and APIKey:

            # Check if API for the same GST was hit before (stores every API hit in database to reduce cost per hit)
            GSTExists = request.env['bs.gst'].sudo().search([('name','=',GSTIN)], limit=1)
            City, District, State, Pincode, FullAdd, TradeName, LegalName = '', '', '', '', '','',''
            StateID, DistrictID =  False, False

            if not GSTExists:
                # ---------- GST API --------------
                url = "%s/verify-gst-lite"%(URL)
                payload = "{\n    \"gstin\":\"%s\",\n    \"consent\":\"Y\",\n    \"consent_text\":\"I have given full consent\"\n} "%(GSTIN)
                headers = { 'Content-Type': 'application/json', 'qt_api_key': APIKey, 'qt_agency_id': AgencyKey }
                response = requests.request("POST", url, headers=headers, data=payload)
                res = json.loads(response.text.encode('utf8')).get('result',{})
                # ---------- GST API --------------

                if res :
                    GSTStatus = res.get('sts')
                    TradeName, LegalName = res.get('tradeNam'), res.get('lgnm')
                    GSTLastUpdated, GSTReg = res.get('lstupdt'), res.get('rgdt')
                    Add = res.get('pradr') and res.get('pradr').get('addr', {})

                    if Add:
                        City, District, State, Pincode = Add['city'], Add['dst'], Add['stcd'], Add['pncd']
                        StateID = request.env['res.country.state'].sudo().search([('name','=',State.strip()),('country_id.code','=','IN')],limit=1).id
                        DistrictID = request.env['bs.district'].sudo().search([('name','=',District.strip()),('state_id','=',StateID)],limit=1).id
                        if not DistrictID: DistrictID = request.env['bs.district'].sudo().create({'name':District.strip(),'state_id':StateID}).id

                        if Add['flno']: FullAdd += Add['flno']
                        if Add['bno']: FullAdd += (', ' if Add['flno'] else '') + Add['bno']
                        if Add['bnm']: FullAdd += (', ' if Add['bno'] else '') + Add['bnm']
                        if Add['st']: FullAdd += (', ' if Add['bnm'] else '') + Add['st']
                        if Add['loc']: FullAdd += (', ' if Add['st'] else '') + Add['loc']
                        if Add['city']: FullAdd += (', ' if Add['loc'] else '') + Add['city']
                        if Add['dst']: FullAdd += (', ' if Add['city'] else '') + Add['dst']
                        if Add['stcd']: FullAdd += (', ' if Add['dst'] else '') + Add['stcd']
                        if Add['pncd']: FullAdd += (', ' if Add['stcd'] else '') + Add['pncd']

                    request.env['bs.gst'].sudo().create({'api_response':res, 'registered_address':FullAdd,
                                                         'legal_name':LegalName, 'trade_name':TradeName,
                                                         'name': GSTIN, 'pan':GSTIN[2:12],'pincode':Pincode,
                                                         'reg_date':datetime.strptime(GSTReg, '%d/%m/%Y'),
                                                         'gst_updated_date':datetime.strptime(GSTLastUpdated, '%d/%m/%Y'),
                                                         'gst_status':'active' if GSTStatus == 'Active' else 'inactive',
                                                         'city':City, 'state_id':StateID, 'district_id':DistrictID })
                    return {'reg_add': FullAdd, 'trade_name': TradeName, 'legal_name': LegalName, 'city': City,
                            'district': DistrictID, 'state': StateID, 'pincode': Pincode}
                else: return False

            elif GSTExists: #if system has already captured GST information before
                return {'reg_add': GSTExists.registered_address, 'trade_name': GSTExists.trade_name,
                        'legal_name': GSTExists.legal_name, 'district': GSTExists.district_id.id,
                        'city': GSTExists.city, 'state': GSTExists.state_id.id, 'pincode': GSTExists.pincode}
            else:
                return False
        else: return False

    @http.route('/services', type = "http", auth = "public", website = True)
    def services(self):
        return request.render('builderbay.coming_soon',{'message': 'For Services, please contact'})

    @http.route('/upload/enquiry', type="http", auth="user", website=True)
    def click_and_upload(self, **kw):
        return request.render('builderbay.bs_click_upload')

    @http.route(['/categories','/categories/<string:type>'], type = "http", auth = "public", website = True)
    def all_categories(self, type=''):
        values = {'type':type}
        return request.render('builderbay.bs_all_categs',values)  #TODO: add coming soon

    # Vendor portal starts
    @http.route(['/vendor/dashboard'], type='http', auth='public', website=True, csrf=False)
    def vendorDashboard(self, **post):
        vals = {}

        user = request.env['res.users'].browse(request.uid)
        rfq = request.env['bs.rfq'].sudo().search([('vendor_id', '=', user.partner_id.id), ('state', 'in', ('draft','accept'))])

        vals.update({'rfq': len(rfq)})
        return request.render('builderbay.vendor_dashboard', vals)

    @http.route(['/vendor/signup'], type='http', auth='public', website=True, csrf=False)
    def vendorSignIn(self, **post):
        return request.render('builderbay.bs_signup_login')

    @http.route(['/vendor/new_order'], type='http', auth='public', website=True, csrf=False, sitemap=False)
    def newOrder(self, **post):
        vals = {}
        user = request.env['res.users'].browse(request.uid)
        domain = [('vendor_id', '=', user.partner_id.id), ('state', 'in', ('draft','accept'))]
        if post.get('StartDate') and post.get('EndDate'):
            domain.append(('date_order','>=',post.get('StartDate')))
            domain.append(('date_order','<=',post.get('EndDate')))
        rfq = request.env['bs.rfq'].sudo().search(domain)
        bs_percentage = request.env['ir.config_parameter'].sudo().search([('key','=','bs_percentage')])
        vals.update({'rfq': rfq, 'total': len(rfq), 'bs_percentage': bs_percentage.value})
        return request.render('builderbay.new_order_demo', vals)

    @http.route('/rfq/details', type='json', auth="user", sitemap=False, website=True)
    def rfq_details(self, **kw):
        rfq_id = kw.get('rfq_id')
        html,line_qty,base_price,total,tax_total = request.env['bs.rfq'].getRfqDetails(int(rfq_id))
        return {'rfq_dtls': html,'total_qty':line_qty,'total_bprice':base_price,'rf_total':total, 'tax_total': tax_total}

    @http.route('/rfq/update', type='json', auth="user", sitemap=False, website=True)
    def rfq_update(self, **kw):
        line_id = kw.get('line_id')
        price = kw.get('price')
        tax = kw.get('tax')
        name = kw.get('name')
        vals = request.env['bs.rfq'].update_price(int(line_id), price, tax, name)
        return vals
    
    @http.route('/rfq/accept', type='json', auth="user", sitemap=False, website=True)
    def rfq_accept(self, **kw):
        line_id = kw.get('rfq_id')
        rfq = request.env['bs.rfq'].browse(int(line_id))
        rfq.state = 'accept'
        return {'success': True}
    
    @http.route('/rfq/reject', type='json', auth="user", sitemap=False, website=True)
    def rfq_reject(self, **kw):
        line_id = kw.get('rfq_id')
        rfq = request.env['bs.rfq'].browse(int(line_id))
        rfq.state = 'reject'
        return {'success': True}
    # Vendor portal ends

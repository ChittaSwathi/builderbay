import json
import logging
import pprint
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound
import werkzeug
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.osv import expression
from itertools import combinations
from odoo.addons.website.models import ir_http
from ast import literal_eval
from odoo.tools import pycompat
from werkzeug import urls
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
_logger = logging.getLogger(__name__)
import itertools
from odoo.osv import expression
import requests


class BSWebsiteSale(WebsiteSale):

    def checkout_redirection(self, order):
        # must have a draft sales order with lines at this point, otherwise reset
        if not order or order.state != 'sent':
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.redirect('/shop')

        if order and not order.order_line:
            return request.redirect('/shop/cart')

        # if transaction pending / done: redirect to confirmation
        tx = request.env.context.get('website_sale_transaction')
        if tx and tx.state != 'draft':
            return request.redirect('/shop/payment/confirmation/%s' % order.id)


    @http.route('/safety', type='http', auth="public", website=True, sitemap=False)
    def safety_products(self, **post):
        return request.render("builderbay.safety_products")

    @http.route('/b2b/login', type='http', auth="public", website=True, sitemap=False)
    def bs_b2b_login(self, **post):
        return request.render("builderbay.b2b_login")
    
    ### call back api ###
    @http.route('/payment/callback', type='http', auth="public", csrf=False)
    def payment_callback(self, **post):
        _logger.info('Atom: entering form_callback with post data %s', pprint.pformat(post))
        request.env['payment.transaction'].sudo().atom_callback(post)
        return werkzeug.utils.redirect('/my')
#         request.env['payment.transaction'].sudo().atom_callback(post)
#         return True
    ### end ###

    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id)
            assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
            if not tx and order.transaction_ids:
                tx = order.transaction_ids[0]
        else:
            tx = None

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if order and not order.amount_total and not tx:
            order.with_context(send_email=True).action_confirm()
            return request.redirect(order.get_portal_url())

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        PaymentProcessing.remove_payment_transaction(tx)
        return request.redirect('/shop/confirmation')

    @http.route(['/shop/payment/transaction/',
        '/shop/payment/transaction/<int:so_id>',
        '/shop/payment/transaction/<int:so_id>/<string:access_token>'], type='json', auth="public", sitemap=False, website=True)
    def payment_transaction(self, acquirer_id, save_token=False, so_id=None, access_token=None, token=None, **kwargs):
        """ Json method that creates a `payment.transaction`, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        """
        if kwargs.get('order_id'): so_id = kwargs.get('order_id')

        # Ensure a payment acquirer is selected
        if not acquirer_id: return False
        try: acquirer_id = int(acquirer_id)
        except: return False

        # Retrieve the sale order
        if so_id:
            env = request.env['sale.order']
            domain = [('id', '=', so_id)]
            if access_token:
                env = env.sudo()
                domain.append(('access_token', '=', access_token))
            order = env.search(domain, limit=1)
        else:
            order = request.website.sale_get_order()

        if order:
            request.session['sale_order_id'] = order.id
            request.session['sale_last_order_id'] = order.id

        # Ensure there is something to proceed
        if not order or (order and not order.order_line):
            return False

        assert order.partner_id.id != request.website.partner_id.id

        # Create transaction
        vals = {'acquirer_id': acquirer_id, 'return_url': '/shop/payment/validate'}
        if save_token: vals['type'] = 'form_save'
        if token: vals['payment_token_id'] = int(token)
        if kwargs.get('utr_no'): vals.update(utr_no = kwargs.get('utr_no')) #NEFT
        transaction = order._create_payment_transaction(vals)

        # store the new transaction into the transaction list and if there's an old one, we remove it
        # until the day the ecommerce supports multiple orders at the same time
        last_tx_id = request.session.get('__website_sale_last_tx_id')
        last_tx = request.env['payment.transaction'].browse(last_tx_id).sudo().exists()
        if last_tx:
            PaymentProcessing.remove_payment_transaction(last_tx)
        PaymentProcessing.add_payment_transaction(transaction)
        request.session['__website_sale_last_tx_id'] = transaction.id

        return transaction.render_sale_button(order)

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        sale_order_id = request.session.get('sale_last_order_id') or \
                        (request.website.sale_get_order().id if request.website.sale_get_order() else False)
        if sale_order_id:
            SaleOrder = request.env['sale.order'].sudo().browse(sale_order_id)
            SaleOrder.write({'payment_processed': True})
            Txn = SaleOrder.transaction_ids[0] if SaleOrder.transaction_ids else False
            if Txn and Txn.state == 'done':
                if Txn.payment_id and Txn.payment_id.state == 'posted':
                    SaleOrder.write({'paid': True, 'unpaid': False})
                    try:
                        if SaleOrder.website_id:
                            EnableOutgSMS = bool(
                                request.env['ir.config_parameter'].sudo().get_param('bs.outgng_sms', False))
                            EnableOutgMail = bool(
                                request.env['ir.config_parameter'].sudo().get_param('bs.outgng_mail', False))

                            # Customer notification
                            if EnableOutgSMS:
                                Message = 'Your payment has been received for order %s. In case of any clarification, please email us at %s / call %s.' % (
                                    SaleOrder.name, SaleOrder.company_id.cust_care_email,
                                    SaleOrder.company_id.cust_care_phone)
                                url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (
                                    SaleOrder.company_id.sms_apikey)
                                headers = {
                                    'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                                params = {
                                    "msisdn": SaleOrder.partner_id.mobile,
                                    "sms": Message,
                                    "unicode": "0",
                                    "senderid": SaleOrder.company_id.sms_senderid,
                                    "pingbackurl": "https://builderbay.com/pingback/sms"
                                }
                                requests.post(url, params, headers=headers)
                            if EnableOutgMail:
                                Message = 'Your payment has been received for order %s. In case of any clarification, please email us at %s / call %s.' % (
                                    SaleOrder.name, SaleOrder.company_id.cust_care_email,
                                    SaleOrder.company_id.cust_care_phone)
                                mail_values = {'email_from': 'info@builderbay.com',
                                               'email_to': SaleOrder.partner_id.email,
                                               'subject': "Payment Received - %s"%(SaleOrder.name),
                                               'body_html': Message,
                                               'state': 'outgoing'}
                                mail = request.env['mail.mail'].sudo().create(mail_values)
                                mail.sudo().send(True)

                            # Backend team notification: TODO: switch control
                            SPEmail = SaleOrder.sudo().user_id.partner_id.email or SaleOrder.sudo().user_id.login
                            SPMobile = SaleOrder.sudo().user_id.partner_id.mobile
                            if SPEmail:
                                Message = 'Payment has been successfully made for Order %s by customer %s.' % (
                                    SaleOrder.name, SaleOrder.partner_id.name)
                                mail_values = {'email_from': 'info@builderbay.com',
                                               'email_to': SPEmail,
                                               'subject': "Payment Received - %s"%(SaleOrder.name),
                                               'body_html': Message,
                                               'state': 'outgoing'}
                                mail = request.env['mail.mail'].sudo().create(mail_values)
                                mail.sudo().send(True)
                            if SPMobile:
                                Message = 'Payment has been successfully made for Order %s by customer %s.' % (
                                    SaleOrder.name, SaleOrder.partner_id.name)
                                url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (
                                    SaleOrder.company_id.sms_apikey)
                                headers = {
                                    'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                                params = {
                                    "msisdn": SPMobile,
                                    "sms": Message,
                                    "unicode": "0",
                                    "senderid": SaleOrder.company_id.sms_senderid,
                                    "pingbackurl": "https://builderbay.com/pingback/sms"
                                }
                                requests.post(url, params, headers=headers)
                    except Exception as E:
                        print(E)
                elif not Txn.payment_id:
                    SaleOrder.write({'paid': False, 'unpaid': True})
            return request.render("website_sale.confirmation", {'order': SaleOrder})
        else:
            return request.redirect('/shop')

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        order = False
        if post.get('order_ids'): order = request.env['sale.order'].sudo().browse(int(post.get('order_ids')))
        else: return request.redirect('/shop/cart')

        if not order: order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False

        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')

        render_values['order_id'] = order.id
        render_values['callback_method'] = 'test_callback'
        return request.render("website_sale.payment", render_values)

    def _get_shop_payment_values(self, order, **kwargs):
        values = dict(
            website_sale_order=order,
            errors=[],
            partner=order.partner_id.id,
            order=order,
            payment_action_id=request.env.ref('payment.action_payment_acquirer').id,
            return_url= '/shop/payment/validate',
            bootstrap_formatting= True
        )

        PartnerGroup = request.env.user.partner_id.customer_type
        if PartnerGroup:
            PartnerGroupFilter = [('customer_type', 'in', [PartnerGroup, 'both'])]
        else:
            PartnerGroupFilter = [('customer_type', '=', 'both')]
        domain = expression.AND([
            ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order.company_id.id)],
            ['|', ('website_id', '=', False), ('website_id', '=', request.website.id)],
            ['|', ('country_ids', '=', False), ('country_ids', 'in', [order.partner_id.country_id.id])],
            PartnerGroupFilter
        ])
        acquirers = request.env['payment.acquirer'].search(domain)

        values['access_token'] = order.access_token
        values['acquirers'] = [acq for acq in acquirers if (acq.payment_flow == 'form' and acq.view_template_id) or
                                    (acq.payment_flow == 's2s' and acq.registration_view_template_id)]
        values['tokens'] = request.env['payment.token'].search([
            ('acquirer_id', 'in', acquirers.ids),
            ('partner_id', 'child_of', order.partner_id.commercial_partner_id.id)])

        if order:
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order.amount_total, order.currency_id, order.partner_id.country_id.id)
        return values
    #
    # def checkout_redirection(self, order):
    #     # must have a draft sales order with lines at this point, otherwise reset
    #     if not order or order.state != 'accept':
    #         request.session['sale_order_id'] = None
    #         request.session['sale_transaction_id'] = None
    #         return request.redirect('/shop/cart')
    #
    #     if order and not order.order_line:
    #         return request.redirect('/shop/cart')
    #
    #     # if transaction pending / done: redirect to confirmation
    #     tx = request.env.context.get('website_sale_transaction')
    #     if tx and tx.state != 'draft':
    #         return request.redirect('/shop/payment/confirmation/%s' % order.id)

    # @http.route('/redirect/cart', type="json", auth="user", website=False)
    # def bs_redirect_cart(self, **post):
    #     print('redirect cart', post)
    #     self.cart(order_id=post.get('orders')[0])

    # @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    # def cart(self, access_token=None, revive='', **post):
    #
    #     OrderId = int(post.get('order_ids')) if post.get('order_ids') else False
    #     """
    #     Main cart management + abandoned cart revival
    #     access_token: Abandoned cart SO access token
    #     revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
    #     """
    #     if OrderId: order = request.env['sale.order'].sudo().browse(OrderId)
    #     else: order = request.website.sale_get_order()
    #
    #     if order and order.state != 'accept':
    #         request.session['sale_order_id'] = None
    #         order = request.website.sale_get_order()
    #     values = {}
    #     if access_token:
    #         abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
    #         if not abandoned_order:  # wrong token (or SO has been deleted)
    #             raise NotFound()
    #         if abandoned_order.state != 'draft':  # abandoned cart already finished
    #             values.update({'abandoned_proceed': True})
    #         elif revive == 'squash' or (revive == 'merge' and not request.session.get(
    #                 'sale_order_id')):  # restore old cart or merge with unexistant
    #             request.session['sale_order_id'] = abandoned_order.id
    #             return request.redirect('/shop/cart')
    #         elif revive == 'merge':
    #             abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
    #             abandoned_order.action_cancel()
    #         elif abandoned_order.id != request.session.get(
    #                 'sale_order_id'):  # abandoned cart found, user have to choose what to do
    #             values.update({'access_token': abandoned_order.access_token})
    #
    #     values.update({
    #         'website_sale_order': order,
    #         'date': fields.Date.today(),
    #         'suggested_products': [],
    #     })
    #     if order:
    #         order.order_line.filtered(lambda l: not l.product_id.active).unlink()
    #         _order = order
    #         if not request.env.context.get('pricelist'):
    #             _order = order.with_context(pricelist=order.pricelist_id.id)
    #         values['suggested_products'] = _order._cart_accessories()
    #
    #     if post.get('type') == 'popover':
    #         # force no-cache so IE11 doesn't cache this XHR
    #         return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})
    #
    #     return request.render("website_sale.cart", values)

    # Overridden - Multi terms in one
    @http.route(['/terms','/shop/terms'], type='http', auth="public", website=True)
    def terms(self, **kw):
        return request.render("website_sale.terms")

    def _get_search_domain(self, search, category, attrib_values, search_in_description=True,
                           attribCat_values=[]):
        Partner = request.env.user.partner_id
        domains = [request.website.sale_product_domain()]
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                    [('product_variant_ids.default_code', 'ilike', srch)],
                ]
                if search_in_description:
                    subdomains.append([('description', 'ilike', srch)])
                    subdomains.append([('description_sale', 'ilike', srch)])
                domains.append(expression.OR(subdomains))

        # domains.append([('customer_type','in',[Partner.customer_type, 'both'])])
        # if category:
        #     domains.append([('public_categ_ids', 'child_of', int(category))])
        if category and not attribCat_values:
            domains.append([('public_categ_ids', 'child_of', int(category))])

        elif attribCat_values:
            domains.append([('public_categ_ids', 'in', attribCat_values)])
        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if request.env['product.attribute.value'].browse(value[0]).customer_type in [Partner.customer_type,
                                                                                             'both']:
                    if not attrib:
                        attrib = value[0]
                        ids.append(value[1])
                    elif value[0] == attrib:
                        ids.append(value[1])
                    else:
                        domains.append([('attribute_line_ids.value_ids', 'in', ids)])
                        attrib = value[0]
                        ids = [value[1]]
            if attrib:
                domains.append([('attribute_line_ids.value_ids', 'in', ids)])
        return expression.AND(domains)

    @http.route([
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>''',
    ], type='http', auth="public", website=True, sitemap=False)
    def bs_unused_routes(self, page=0, category=None):
        return False

    @http.route([
            '''/shop''',
            '''/shop/page/<int:page>''',
            "/<model('product.public.category'):category>",
            "/<path:path>/<model('product.public.category'):category>",
            "/<path:path>/<model('product.public.category'):category>/page/<int:page>"
            ], type='http', auth="public", website=True, sitemap=True, csrf=False)
    def bs_shop(self, page=0, category=None, search='', ppg=False, path="", **post):
        add_qty = int(post.get('add_qty', 1))
        
        Partner = request.env.user.partner_id
        
        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category)),('customer_type','in',[Partner.customer_type,
                                                                                          'both'])], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = 21
            # ppg = request.env['website'].get_current_website().shop_ppg or 20
        ppr = request.env['website'].get_current_website().shop_ppr or 4

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        # Filter : Sub Category
        attribCat_list = request.httprequest.args.getlist('attribCat')
        attribCat_values = [int(x) for x in attribCat_list]
        attribCat_set = {v for v in attribCat_values}

        domain = self._get_search_domain(search=search, category=category, attrib_values=attrib_values,
                                         search_in_description=True, attribCat_values=attribCat_values)
        print(domain)
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list,
                        attribCat = attribCat_list, order=post.get('order'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list
        if attribCat_list:
            post['attribCat'] = attribCat_list

        Product = request.env['product.template'].with_context(bin_size=True)

        search_product = Product.search(domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search([('product_tmpl_ids', 'in', search_product.ids),
                                                 ('customer_type','in',[Partner.customer_type, 'both'])] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = category.get_recursive_url() #"/shop/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        if category: CurSelCatgs = Category.browse(list(set([category.id] + attribCat_values)))
        else: CurSelCatgs = Category.browse(list(set(attribCat_values)))

        # Respective product Brands for Shop page
        ProdBrandRecs = {}
        for i in products:
            BrandVals = i.attribute_line_ids.filtered(lambda x: x.attribute_id.id == request.env.ref('builderbay.brand_attribute').id).mapped('value_ids')
            if BrandVals: ProdBrandRecs[i.id] = BrandVals[0]
            
        ### search 
        SearchLabel = post.get('search_product', False)
        search_Category = post.get('selected_categ',False)
#         header_render = False
        if SearchLabel:
#             header_render = request.env['ir.qweb']._render('builderbay.bs_header', {'searchLabel':SearchLabel,'res_company':request.env.user.company_id,'user_id':request.env.user})
            search_data = self.bs_header_search(post)
            if search_data.get('products', False):
                products = search_data.get('products')
                product_count = len(products)
                pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
                brands_srch = products.attribute_line_ids.filtered(lambda x: x.attribute_id.id == request.env.ref('builderbay.brand_attribute').id).mapped('value_ids')
            else:
                products = request.env['product.template']
                product_count = len(products)
                pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
            
        #### search code end ###

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,

            #custom
            'sub_categories': Category.search([('parent_id','=',int(category)),('customer_type','in',
                            [Partner.customer_type, 'both'])]) if category else
                Category.search([('parent_id','=',False),('customer_type','in',[Partner.customer_type, 'both'])]),
            'sibling_categs': products.mapped('public_categ_ids') if SearchLabel and products else Category.search([('customer_type','in',[Partner.customer_type, 'both']),
                                               ('parent_id','in', CurSelCatgs.mapped('parent_id.id'))]) or
                              categs.mapped('child_id'),
            'child_categs': products.mapped('public_categ_ids').mapped('child_id') if SearchLabel and products else CurSelCatgs.mapped('child_id'),
            'all_brands': brands_srch if SearchLabel and products else Category.get_brands(eCommCategIDs=CurSelCatgs) or Category.get_brands(eCommCategIDs=categs),
            'product_brands': ProdBrandRecs,
            'selected_categ' : CurSelCatgs[0] if CurSelCatgs else False,

            'attribCat_values': attribCat_values,
            'attribCat_set': attribCat_set,
            'search_Category': request.env['bs.header.search'].sudo().browse(int(search_Category)).name if search_Category else False,
            'SearchLabel':SearchLabel,
            
        }
        if category:
            values['main_object'] = category

        if category:
            if category.l2_view:
                EcommCategObj = request.env['product.public.category'].sudo()
                values = {'sibling_categs': EcommCategObj.search([('parent_id', 'in', [category.parent_id.id]
                                              if category.parent_id else []),
                                              ('customer_type', 'in', [category.parent_id.customer_type, 'both'])]),
                          'child_categs': category.child_id,
                          'trending_categs': EcommCategObj.search([('parent_id', 'child_of', category.id),
                                                                   ('is_trending', '=', True)], limit=6),
                          'ecomm_categ': category,
                          'all_brands': EcommCategObj.get_brands(eCommCategIDs=[category]),
                          'featured_products': request.env['product.template'].sudo().search(
                              [('is_hot_deal', '=', True), ('public_categ_ids', 'child_of', category.id)]),
                          'top_brands': request.env['product.public.category'].sudo().get_brands(
                              eCommCategIDs=[category.id]).filtered(lambda x: x.is_top_brand),
                          'main_object': values['main_object']
                          }
                if category.l2_view == 'tile_view':
                    return request.render('builderbay.bs_l2_tile_view', values)
                elif category.l2_view == 'ecomm_view':
                    return request.render('builderbay.bs_ecommerce_template', values)
                elif category.l2_view == 'brand_view':
                    return request.render('builderbay.bs_l2_page', values)
                else: pass
            # else:
            #     if category.l2_view == 'ecomm_view':
            #         return request.render("builderbay.bs_ecomm_products", values) #TODO:Ecomm products view
#         print(values.get('sub_categories'))
#         values['sub_categories'] = request.env['product.public.category']
        return request.render("builderbay.bs_plp_page", values)

    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        Partner = request.env.user.partner_id
        Transport2site, unloadAtSite, DisplayButtons = False, False, True
        RejectionReasons = request.env['bs.rejection.reason'].sudo().search([])
        SO = False
        HamaliCharges = request.env.ref('builderbay.hamali_charges')
        TransportCharges = request.env.ref('builderbay.transport_charges')
        source = request.httprequest.args.getlist('source')[0] if request.httprequest.args.getlist('source') else None
        AllOrders = request.env['sale.order'].sudo().search([('product_tmpl_id','=',product.id),
                                                      ('partner_id','=',request.env.user.partner_id.id),
                                                      ('state','not in',['cancel','expire','reject']),
                                                      ], order='id desc').\
            filtered(lambda x: x.validity_date and x.validity_date >= datetime.now())
        wh_domain = [('order_id','=',False)]
        if source: #Redirecting to another SO
            SO = request.env['sale.order'].sudo().browse(int(source))
            unloadAtSite = SO.order_line.filtered(lambda x: x.product_id.id == HamaliCharges.id)
            Transport2site = SO.order_line.filtered(lambda x: x.product_id.id == TransportCharges.id)
            DisplayButtons = True,#False if SO.order_line.filtered(lambda x: x.product_id.type != 'product') else True
            wh_domain = [('order_id','=',SO.id)]

        PubCatObj = request.env['product.public.category'].sudo()
        BrandAttrLine = request.env['product.template.attribute.line'].sudo().search([('product_tmpl_id','=',product.id),
                                    ('attribute_id','=',request.env.ref('builderbay.brand_attribute').id)],limit=1)
        StandardVals = self._prepare_product_values(product, category, search, **kwargs)
        StandardVals.update({'exclude_products': []})
        if HamaliCharges:
            StandardVals['exclude_products'] += [HamaliCharges.id]
        if TransportCharges:
            StandardVals['exclude_products'] += [TransportCharges.id]

        StandardVals.update({'brand': BrandAttrLine.value_ids[0] if BrandAttrLine else False,
                             'product_rating': product.sudo().rating_get_stats()})
        defaultAttr = []
#         qty_box = False
        print(kwargs)
        AttributeIDs = []
        if kwargs:
            if kwargs.get('attribute', False):
                AttributeIDs = eval(kwargs['attribute'])
            if kwargs.get('rfq_data', False):
                attribute_qty = {}
                if ',' in kwargs['rfq_data']:
                    chunks = kwargs['rfq_data'].split(',')
                    for chunk in chunks:
                        chnk = chunk.split('_')
                        attribute_qty.update({int(chnk[0]):int(chnk[1])})
                else:
                    chnk = kwargs['rfq_data'].split('_')
                    attribute_qty.update({int(chnk[0]):int(chnk[1])})
                
                StandardVals.update({'attribute_qty':attribute_qty })
            if kwargs.get('rfq_date', False):
                StandardVals.update({'rfq_date':kwargs.get('rfq_date') })
            if kwargs.get('pin', False):
                StandardVals.update({'pin':kwargs.get('pin') })
            if kwargs.get('hamali_charges', False):
                StandardVals.update({'hamali_charges_rfq':kwargs.get('hamali_charges') })
            if kwargs.get('transport_charges', False):
                StandardVals.update({'transport_charges_rfq':kwargs.get('transport_charges') })
            if kwargs.get('reqested_delivery_slot', False):
                StandardVals.update({'reqested_delivery_slot':kwargs.get('reqested_delivery_slot') })
                
        if AttributeIDs:
            Attributes = len(product.attribute_line_ids.mapped('attribute_id.id'))
            ProdVariants = product.product_variant_ids 
            Combs = []
            for i in itertools.combinations(AttributeIDs, Attributes):
                i = set(i)
                if len(i)==Attributes and i not in Combs: Combs += [i]
     
            ToDisplayProds = ProdVariants.filtered(lambda x: set(x.product_template_attribute_value_ids.mapped('product_attribute_value_id.id')) in Combs)
            if ToDisplayProds:
                qty_box = True
                print(ToDisplayProds)
                StandardVals.update({'qty_box': qty_box,'d_product':ToDisplayProds})
            attibute_obj = request.env['product.attribute.value'].browse(list(AttributeIDs))
            StandardVals.update({'d_attributes': list(AttributeIDs),'attibute_obj':attibute_obj})
            
        WishlistedProducts = request.env['customer.wishlist'].sudo().search([('partner_id','=',Partner.id),('state','=','open')]+wh_domain).mapped('product_tmpl_id.id')
        if product.public_categ_ids:
            CategTemps = [categ.pdp_template_id.id for categ in product.public_categ_ids]
            StandardVals.update({'sibling_categs': PubCatObj.search([('parent_id', 'in', product.public_categ_ids[
                0].mapped('parent_id.id')),('customer_type','in',[Partner.customer_type, 'both'])]),
                                 'child_categs': product.public_categ_ids[0].child_id,
                                 'ecomm_categ':product.public_categ_ids[0],
                                 'banners': product.public_categ_ids[0].banner_ids if product.public_categ_ids else False,
                                 'all_brands': PubCatObj.get_brands(eCommCategIDs=[product.public_categ_ids[0].id]),
                                 'sale_order': SO,
                                 # 'rfq_call_url': http.request.httprequest.url,
                                 'transport_charges':Transport2site,
                                 'hamali_charges':unloadAtSite,
                                 'add_brands_data': self.get_brands_grades(product, False) if request.env.ref('builderbay.bs_electricals_qty_box').id not in CategTemps
                                    else self.get_brands_grades(product, True),
                                 'BrandAttrID': request.env.ref('builderbay.brand_attribute').id,
                                 'so_reject_reasons': RejectionReasons,
                                 'district_ids':request.env['bs.district'].sudo().search([]),
                                 'state_ids': request.env['res.country.state'].sudo().search([('country_id.code','=','IN')]),
                                 'gst_ids': request.env['bs.gst'].sudo().search([('partner_id','=',request.env.user.partner_id.id)]),
                                 'past_orders' : AllOrders,
                                 'display_buttons': DisplayButtons,
                                 'wishlisted': WishlistedProducts,
                                })
        if SO: StandardVals.update({'acquirers': self._get_shop_payment_values(SO).get('acquirers',False)})
        CustType = request.env.user.partner_id.customer_type
        ProdCustType = product.customer_type
        if product.is_bulk_cement:
            if CustType == 'b2b': return request.render('builderbay.bulk_cement_pdp', StandardVals)
            else: return request.render('builderbay.b2b_login')
        else:
            if ProdCustType == 'b2b':
                if CustType == 'b2b': return request.render('builderbay.bs_pdp_page2', StandardVals)
                else: return request.render('builderbay.b2b_login')
            else:
                return request.render('builderbay.bs_pdp_page2', StandardVals)



    @http.route('/checkout_list', type="json", auth="user", website=False)
    def checkout_list(self, **post):
        """ Return dict of checkout order details """
        order_ids = post.get('order_ids')
        order_details = request.env['sale.order'].checkout_orders(order_ids)
        return order_details
    
    @http.route(['/shop/cart'], type='http', auth="user", website=True, sitemap=False)
    def bs_cart(self, **post):
        user = request.env['res.users'].browse(request.uid)
        order_details = request.env['sale.order'].sudo().customer_cart(user)
        return request.render("builderbay.bs_cart",order_details)

    @http.route(['/uom/conversion'], type='json', auth="public", methods=['POST'], sitemap=False,website=True)
    def uom_conversion(self, **kw):
        ProductID, UOMID, Qty = kw.get('product_id',False), kw.get('uom_id',False), kw.get('qty','0')
        AllConvVals = {}
        AttrValue = request.env['product.product'].browse(int(ProductID)).product_template_attribute_value_ids.filtered(lambda x: x.attribute_id.has_unit_conversion).mapped('product_attribute_value_id.id')

        if AttrValue and UOMID and Qty:
            Convs = request.env['product.attribute.value'].browse(int(AttrValue[0])).uom_convrsn_ids
            FromConvs = Convs.filtered(lambda x: x.from_uom_id.id == int(UOMID))

            for i in FromConvs:
                # Retaining UOM data type
                if i.to_uom_id.data_type == 'int':ConvQty = int(Qty * i.to_value)
                else: ConvQty = '%.3f'%(float(Qty) * i.to_value)
                AllConvVals[i.to_uom_id.id] = (i.to_uom_id.name, ConvQty)

        return AllConvVals

    @http.route('/show_variant_list', type="json", auth="none", website=False)
    def show_variant_list(self, **post):
        """ Returns list of variants that should be displayed in frontend based on selected attributes """
        final_uri_preview = "/web/static/src/img/placeholder.png"
        
        import re
        single_comb_prod = True
        AttributeIDs = post.get('attribute_ids')
        ProdTemplObj = request.env['product.template'].browse(int(post.get('product_tmpl_id')))
        Attributes = len(ProdTemplObj.attribute_line_ids.mapped('attribute_id.id'))
        ProdVariants = ProdTemplObj.product_variant_ids
        
        Combs = []
        for i in itertools.combinations(AttributeIDs, Attributes):
            i = set(i)
            if len(i)==Attributes and i not in Combs: Combs += [i]

        ToDisplayProds = ProdVariants.filtered(lambda x: set(x.product_template_attribute_value_ids.mapped('product_attribute_value_id.id')) in Combs)
        try:
            s3 = ['shop']
            public_categ = ToDisplayProds[0].public_categ_ids
            last_cate = "/".join(public_categ.parents_and_self.mapped('name'))
            last_categ=last_cate.replace(" & ","_")
            if last_categ: s3.append(last_categ)
            Brands = ProdTemplObj.attribute_line_ids.filtered(lambda x: x.attribute_id.id == request.env.ref('builderbay.brand_attribute').id).mapped('value_ids')
            if len(ToDisplayProds) != 1:
                single_comb_prod = False
                if Brands:
                    s3.append(Brands.name)
                    s3.append(Brands.name)
            else:
                if Brands:
                    s3.append(Brands.name)
                if ToDisplayProds[0].default_code:
                    s3.append(ToDisplayProds[0].default_code)
                if not ToDisplayProds[0].default_code:
                    s3.append(Brands.name)
            Website_env = request.env['website']
            website = Website_env.get_current_website()
            cdn_url = website.cdn_url
            if not cdn_url:
                final_uri = final_uri_preview
            else:
                uri = '/'.join(s3)
                final_uri = urls.url_join(cdn_url, uri)
                _logger.info('FINAL URL -- %s'%(final_uri))
                response = requests.get(final_uri)
                if response.status_code != 200:
                    if single_comb_prod and ToDisplayProds[0].default_code:
                        s3 = s3[:-1]
                        s3.append(Brands.name)
                        uri = '/'.join(s3)
                        final_uri = urls.url_join(cdn_url, uri)
                        _logger.info('FINAL URL2 -- %s'%(final_uri))
                        response = requests.get(final_uri)
                        if response.status_code != 200:
                            final_uri = final_uri_preview
        except:
            final_uri = final_uri_preview
        return {'displayProd':ToDisplayProds.ids,'image':final_uri}

    @http.route(['/create/rfq'], type='json', auth="user", methods=['POST'], sitemap=False, website=True)
    def create_rfq(self, **kw):
        if type(kw) == str: kw = eval(kw)
        MainProds, OtherProds, VariantProducts = kw.get('main_product'), kw.get('other_products'), kw.get('variant_products')
        ProdTmplID = request.env['product.template'].browse(kw.get('product_template'))
        hamali_charges, transport_charges = kw.get('hamali_charges',False), kw.get('transport_charges',False)
        WebSalesperson = request.env['res.users'].sudo().search([('login','=','prabhanjan@builderbay.com')], limit=1)

        #BulkEnquiry Details
        BulkEnqVals = {}
        if kw.get('bulkenq_vals'):
            BulkEnq = kw.get('bulkenq_vals')
            BulkEnqVals.update(is_bulk_enq= True)
            if BulkEnq.get('project_type'): BulkEnqVals.update(enq_project_type = BulkEnq.get('project_type'))
            if BulkEnq.get('total_requirement'): BulkEnqVals.update(enq_total_req = BulkEnq.get('total_requirement'))
            if BulkEnq.get('monthly_requirement'): BulkEnqVals.update(enq_monthly_req = BulkEnq.get('monthly_requirement'))
            if BulkEnq.get('current_requirement'): BulkEnqVals.update(enq_current_req = BulkEnq.get('current_requirement'))
            if BulkEnq.get('approved_brands'): BulkEnqVals.update(enq_approved_brands = BulkEnq.get('approved_brands'))
            if BulkEnq.get('contact_name'): BulkEnqVals.update(enq_contact_name = BulkEnq.get('contact_name'))
            if BulkEnq.get('phone_number'): BulkEnqVals.update(enq_contact_phone=BulkEnq.get('phone_number'))
            if BulkEnq.get('email'): BulkEnqVals.update(enq_contact_email=BulkEnq.get('email'))
            if BulkEnq.get('delivery_address'): BulkEnqVals.update(enq_del_address=BulkEnq.get('delivery_address'))
            if BulkEnq.get('landmark'): BulkEnqVals.update(enq_landmark=BulkEnq.get('landmark'))
            if BulkEnq.get('city'): BulkEnqVals.update(enq_city=BulkEnq.get('city'))
            if BulkEnq.get('district'): BulkEnqVals.update(enq_district_id=int(BulkEnq.get('district')))
            if BulkEnq.get('state_id'): BulkEnqVals.update(enq_state_id=int(BulkEnq.get('state_id')))
            if BulkEnq.get('pincode'): BulkEnqVals.update(enq_pincode=BulkEnq.get('pincode'))
            if BulkEnq.get('gstin'): BulkEnqVals.update(enq_gstin=BulkEnq.get('gstin'))
            if BulkEnq.get('gst_base64'): BulkEnqVals.update(enq_gst_attachment=request.env['ir.attachment'].sudo().create({'type': 'binary',
                                                                                  'name': BulkEnq.get('gst_attach_name'),
                                                                                  'datas': BulkEnq.get('gst_base64')}).id)
            if BulkEnq.get('registered_address'): BulkEnqVals.update(enq_reg_address=BulkEnq.get('registered_address'))

        if MainProds or OtherProds:
            # Main Products
            SOL = []
            for j in MainProds:
                for i in j:
                    Details = j[i]
                    SOL += [(0,0,{'product_id': int(i),
                                  'product_uom_qty': Details['qty'],
                                  'product_uom': ProdTmplID.uom_id.id,
                                  'price_unit':0})]
            #variants - electricals
            for i in VariantProducts:
                Brands = ProdTmplID.attribute_line_ids.filtered(lambda x: x.attribute_id.id == request.env.ref('builderbay.brand_attribute').id).mapped('value_ids')
                AttribVals = list(map(int, i.get('attrs')))
                if Brands: AttribVals = AttribVals + Brands.ids
                varProd = request.env['product.product'].sudo().search([]).filtered(lambda x: set(x.product_template_attribute_value_ids.mapped('product_attribute_value_id.id')) == set(AttribVals))
                if varProd:
                    varProd = varProd[0]
                    ProdTmpl = varProd.product_tmpl_id
                    SOL += [(0, 0, {'product_id': varProd.id,
                                    'name': varProd.name or ProdTmpl.name,
                                    'product_uom_qty': int(i.get('qty')),
                                    'product_uom': varProd.uom_id.id,
                                    'price_unit':0,
                                   })]
            if hamali_charges: SOL += [(0, 0, {'product_id': request.env.ref('builderbay.hamali_charges').id, 'name': 'Hamali Charges'})]
            if transport_charges: SOL += [(0, 0, {'product_id': request.env.ref('builderbay.transport_charges').id, 'name': 'Transport Charges'})]
            CreateSOVals = {'partner_id': request.env.user.partner_id.id,
                            'order_line': SOL,
                            'state': 'draft',
                            'website_id': ir_http.get_request_website().id,
                            'product_tmpl_id': ProdTmplID.id,
                            'reqested_delivery_slot':kw.get('reqested_delivery_slot','morning').lower() ,
                            'user_id': WebSalesperson.id if WebSalesperson else 1,
                            'payment_term_id': request.env.ref('account.account_payment_term_immediate').id,
                            }
            if BulkEnqVals: CreateSOVals.update(BulkEnqVals)
            SaleOrder = request.env['sale.order'].sudo().create(CreateSOVals)
            if kw.get('requested_del_date',False): SaleOrder.write({'requested_del_date':kw.get('requested_del_date')})

            try:
                if SaleOrder and SaleOrder.website_id: #TODO:switch based sms,email trigger & templates creation
                    EnableOutgSMS = bool(request.env['ir.config_parameter'].sudo().get_param('bs.outgng_sms', False))
                    EnableOutgMail = bool(request.env['ir.config_parameter'].sudo().get_param('bs.outgng_mail', False))
                    Emails2Notify = request.env['ir.config_parameter'].sudo().get_param('bs.notify_rfq_emails', '')
                    SMS2Notify = request.env['ir.config_parameter'].sudo().get_param('bs.notify_rfq_sms', '')
                    Emails2Notify_on = request.env['ir.config_parameter'].sudo().get_param('bs.outgng_mail_inusr',False)
                    SMS2Notify_on = request.env['ir.config_parameter'].sudo().get_param('bs.outgng_sms_inusr',False)

                    #Customer notification
                    if EnableOutgSMS:
                        Message = 'Your price enquiry has been placed successfully, we shall revert shortly with price quotation. In case of support, email us at %s / call %s.' % (SaleOrder.company_id.cust_care_email,SaleOrder.company_id.cust_care_phone)
                        url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (SaleOrder.company_id.sms_apikey)
                        headers = {'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                        params = {
                            "msisdn": SaleOrder.partner_id.mobile,
                            "sms": Message,
                            "unicode": "0",
                            "senderid": SaleOrder.company_id.sms_senderid,
                            "pingbackurl": "https://builderbay.com/pingback/sms"
                        }
                        SMSResp = requests.post(url, params, headers=headers)
                    if EnableOutgMail:
                        Message = 'Your price enquiry has been placed successfully, we shall revert shortly with price quotation. In case of any further clarification, please email us at %s / call %s.' % (SaleOrder.company_id.cust_care_email,SaleOrder.company_id.cust_care_phone)
                        mail_values = {'email_from': 'info@builderbay.com',
                                       'email_to': SaleOrder.partner_id.email,
                                       'subject': "Price Enquiry Placed",
                                       'body_html': Message,
                                       'state': 'outgoing'}
                        mail = request.env['mail.mail'].sudo().create(mail_values)
                        MailResp = mail.sudo().send(True)

                    # Backend team notification -- from General settings
                    if Emails2Notify and Emails2Notify_on:
                        subject = "New RFQ generated"
                        Message = 'New RFQ has been generated with Ref #%s. Please update and process it soon.'%(SaleOrder.name)
                        mail_values = {'email_from': 'info@builderbay.com',
                                       'email_to': Emails2Notify,
                                       'subject': subject,
                                       'body_html': Message,
                                       'state': 'outgoing'}
                        mail = request.env['mail.mail'].sudo().create(mail_values)
                        mail.sudo().send(True) #control based on new config switch
                    if SMS2Notify and SMS2Notify_on:
                        Message ='New RFQ has been generated with Ref #%s. Please update and process it soon.'%(SaleOrder.name)
                        url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (SaleOrder.company_id.sms_apikey)
                        headers = {'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                        params = {
                            "msisdn": SMS2Notify,
                            "sms": Message,
                            "unicode": "0",
                            "senderid": SaleOrder.company_id.sms_senderid,
                            "pingbackurl": "https://builderbay.com/pingback/sms"
                        }
                        requests.post(url, params, headers=headers)

            except Exception as e:
                print('Exception occurred',e)

            if kw.get('other_vals'):
                if kw.get('other_vals').get('logo_attachment'):
                    LogoAttach = request.env['ir.attachment'].sudo().create({'type': 'binary',
                                                                'name': 'LogoAttachment',
                                                                'datas': kw.get('other_vals').get('logo_attachment')})
                    if LogoAttach: SaleOrder.write({'logo_attachment': LogoAttach.id})
                SaleOrder.write({'logo_tagline': kw.get('other_vals').get('logo_tagline')})
            return SaleOrder.id
        return False

    @http.route(['/confirm/so'], type='json', auth="public", methods=['POST'], sitemap=False, website=True)
    def confirm_so(self, **kw):
        SaleOrder = kw.get('order_id')
        SaleOrderRec = request.env['sale.order'].sudo().browse(int(SaleOrder))
        request.env['sale.order'].sudo().browse(int(SaleOrder)).write({'state':'done'})
        return SaleOrderRec.name

#     @http.route('/bs/search', type='http', auth="public", website=True, sitemap=False)
    def bs_header_search(self, kw):
        Partner = request.env.user.partner_id
        Category = kw.get('selected_categ',False)
        SearchLabel = kw.get('search_product')
        CategoryObj = request.env['product.public.category'].sudo()
        Domain, Categories = [('is_published','=',True)], CategoryObj.search([('customer_type','in',[Partner.customer_type, 'both'])])
        if SearchLabel:
            for srch in SearchLabel.split(" "):
                Domain += expression.OR([['|',('name', 'ilike', srch),('product_variant_ids.default_code', 'ilike', srch)]])

        if Category:
            Categories = request.env['bs.header.search'].sudo().browse(int(Category)).categ_ids
            if Categories: Domain += expression.OR([[('public_categ_ids', 'child_of', Categories.ids)]])

        AllProducts = request.env['product.template'].sudo().search(Domain)
        # Respective product Brands for Shop page
        ProdBrandRecs = {}
        for i in AllProducts:
            BrandVals = i.attribute_line_ids.filtered(
                lambda x: x.attribute_id.id == request.env.ref('builderbay.brand_attribute').id).mapped(
                'value_ids')
            if BrandVals: ProdBrandRecs[i.id] = BrandVals[0]

        values = {
            'products': AllProducts,
            'sub_categories': CategoryObj.search([('parent_id', 'in', Categories.ids),('customer_type','in',
                                                                                       [Partner.customer_type, 'both'])]),
            'sibling_categs': CategoryObj.search([('parent_id', 'in', Categories.mapped('parent_id.id')),
                                                  ('customer_type','in',[Partner.customer_type, 'both'])]),
            'child_categs': Categories.mapped('child_id'),
            'all_brands': CategoryObj.get_brands(eCommCategIDs=Categories),
            'product_brands': ProdBrandRecs,
            # 'primary_brands': CategoryObj.get_brands(eCommCategIDs=Categories).filtered(lambda x: x.hierarchy_type == 'prime'),
            # 'secondary_brands': CategoryObj.get_brands(eCommCategIDs=Categories).filtered(lambda x: x.hierarchy_type == 'second')
        }
        return values


    # @http.route(['/brands/grades'], type='json', auth="public", methods=['POST'], website=True)
    # def get_brands_grades(self, Product):
    #     ''' Fetches brands, grades of all ecomm categories assigned to cement product '''
    #     FinalVals = {}
    #     BrandAttr = request.env.ref('builderbay.brand_attribute').id
    #     GradeAttr = request.env.ref('builderbay.grade_attribute').id
    #     ProductIDs = request.env['product.template'].search(
    #                         ['|', ('public_categ_ids', 'child_of', Product.public_categ_ids.ids),
    #                          ('public_categ_ids', 'in', Product.public_categ_ids.ids)] if Product else [])
    #     for Prod in ProductIDs:
    #         Attributes =  Prod.attribute_line_ids.mapped('attribute_id.id')
    #         if (BrandAttr in Attributes) and (GradeAttr in Attributes):
    #             Brand = Prod.attribute_line_ids.filtered(lambda x: x.attribute_id.id == BrandAttr)
    #
    #             for i in Brand.value_ids:
    #                 if i in FinalVals:
    #                     FinalVals[i] += [Prod.attribute_line_ids.filtered(lambda x: x.attribute_id.id == GradeAttr).value_ids]
    #                 else:
    #                     FinalVals[i] = [Prod.attribute_line_ids.filtered(lambda x: x.attribute_id.id == GradeAttr).value_ids]
    #     return FinalVals

    @http.route(['/brands/grades'], type='json', auth="public", methods=['POST'],sitemap=False, website=True)
    def get_brands_grades(self, Product, SameTemplate):
        ''' Fetches brands, grades of all ecomm categories assigned to cement product '''
        FinalVals = {}
        Partner = request.env.user.partner_id
        ProductIDs = request.env['product.template'].search(
            [('public_categ_ids', 'child_of',Product.public_categ_ids.ids),
             ('public_categ_ids', 'in', Product.public_categ_ids.ids)] if Product else [])
        Attributes = Product.attribute_line_ids.mapped('attribute_id.id')

        if not SameTemplate:
            ProductIDs = ProductIDs.filtered(lambda x: x.id != Product.id)
            for Prod in ProductIDs:
                ProdAttrs = Prod.attribute_line_ids.mapped('attribute_id.id')
                if (set(Attributes) == set(ProdAttrs)):
                    for attr in Prod.attribute_line_ids:
                        if attr.attribute_id in FinalVals:
                            for atval in attr.value_ids:
                                if atval.customer_type in ['both', Partner.customer_type]:
                                    FinalVals[attr.attribute_id] += [atval.id]
                        else:
                            for atval in attr.value_ids:
                                if atval.customer_type in ['both', Partner.customer_type]:
                                    FinalVals[attr.attribute_id] = [atval.id]
        else:
            for i in Product.attribute_line_ids:
                FinalVals[i.attribute_id] = i.value_ids.ids

        FinalVals = {i: request.env['product.attribute.value'].browse(list(set(FinalVals[i]))) for i in FinalVals}
        return FinalVals

    @http.route(['/reject/so'], type='json', auth="public", methods=['POST'], sitemap=False,website=True)
    def bs_customer_reject_so(self, **kw):
        if kw.get('order_id'):
            Orders = request.env['sale.order'].browse(int(kw.get('order_id'))).with_user(request.env.user)
            ReturnResp =  Orders.write({'state': 'reject',
                                     'rejection_info': kw.get('reason'),
                                     'rejection_reason': int(kw.get('reason_id'))})

            try:
                for SaleOrder in Orders:
                    if SaleOrder and SaleOrder.website_id:
                        EnableOutgSMS = bool(
                            request.env['ir.config_parameter'].sudo().get_param('bs.outgng_sms', False))
                        EnableOutgMail = bool(
                            request.env['ir.config_parameter'].sudo().get_param('bs.outgng_mail', False))

                        # Customer notification
                        if EnableOutgSMS:
                            Message = 'Your order has been successfully rejected %s, In case of support, please email us at %s / call %s.'%(
                            SaleOrder.name, SaleOrder.company_id.cust_care_email, SaleOrder.company_id.cust_care_phone)
                            url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (
                                SaleOrder.company_id.sms_apikey)
                            headers = {'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                            params = {
                                "msisdn": SaleOrder.partner_id.mobile,
                                "sms": Message,
                                "unicode": "0",
                                "senderid": SaleOrder.company_id.sms_senderid,
                                "pingbackurl": "https://builderbay.com/pingback/sms"
                            }
                            requests.post(url, params, headers=headers)
                        if EnableOutgMail:
                            Message = 'Your order has been successfully rejected %s, In case of support, please email us at %s / call %s.'%(
                            SaleOrder.name, SaleOrder.company_id.cust_care_email, SaleOrder.company_id.cust_care_phone)
                            mail_values = {'email_from': 'info@builderbay.com',
                                           'email_to': SaleOrder.partner_id.email,
                                           'subject': "Order Rejected - %s"%(SaleOrder.name),
                                           'body_html': Message,
                                           'state': 'outgoing'}
                            mail = request.env['mail.mail'].sudo().create(mail_values)
                            mail.sudo().send(True)

                        # Backend team notification: TODO: switch control
                        SPEmail = SaleOrder.sudo().user_id.partner_id.email or SaleOrder.sudo().user_id.login
                        SPMobile = SaleOrder.sudo().user_id.partner_id.mobile
                        if SPEmail:
                            Message = 'Quotation %s has been rejected by customer %s.' % (
                            SaleOrder.name, SaleOrder.partner_id.name)
                            mail_values = {'email_from': 'info@builderbay.com',
                                           'email_to': SPEmail,
                                           'subject': "Quotation Rejected - %s"%(SaleOrder.name),
                                           'body_html': Message,
                                           'state': 'outgoing'}
                            mail = request.env['mail.mail'].sudo().create(mail_values)
                            mail.sudo().send(True)
                        if SPMobile:
                            Message = 'Quotation %s has been rejected by customer %s.' % (
                            SaleOrder.name, SaleOrder.partner_id.name)
                            url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (
                                SaleOrder.company_id.sms_apikey)
                            headers = {'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                            params = {
                                "msisdn": SPMobile,
                                "sms": Message,
                                "unicode": "0",
                                "senderid": SaleOrder.company_id.sms_senderid,
                                "pingbackurl": "https://builderbay.com/pingback/sms"
                            }
                            requests.post(url, params, headers=headers)
                return ReturnResp
            except Exception as E:
                print(E)
        return False

    @http.route(['/accept/so'], type='json', auth="public", methods=['POST'], sitemap=False,website=True)
    def bs_customer_accept_so(self, **kw):
        if kw.get('order_ids'):
            Orders = request.env['sale.order'].browse(literal_eval(kw.get('order_ids')))\
                .filtered(lambda x:x.state in ['sale','done']).with_user(request.env.user)
            Orders.write({'state':'accept'})
            try:
                for SaleOrder in Orders:
                    if SaleOrder and SaleOrder.website_id:
                        EnableOutgSMS = bool(
                            request.env['ir.config_parameter'].sudo().get_param('bs.outgng_sms', False))
                        EnableOutgMail = bool(
                            request.env['ir.config_parameter'].sudo().get_param('bs.outgng_mail', False))

                        # Customer notification
                        if EnableOutgSMS:
                            Message = 'Thank you for Order confirmation %s we shall process the same at the earliest possible. In case of any further clarification, please email us at %s / call at %s.'%(SaleOrder.name, SaleOrder.company_id.cust_care_email,SaleOrder.company_id.cust_care_phone)
                            url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (
                                SaleOrder.company_id.sms_apikey)
                            headers = {'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                            params = {
                                "msisdn": SaleOrder.partner_id.mobile,
                                "sms": Message,
                                "unicode": "0",
                                "senderid": SaleOrder.company_id.sms_senderid,
                                "pingbackurl": "https://builderbay.com/pingback/sms"
                            }
                            requests.post(url, params, headers=headers)
                        if EnableOutgMail:
                            Message = 'Thank you for Order confirmation %s we shall process the same at the earliest possible. In case of any further clarification, please email us at %s / call at %s.'%(SaleOrder.name, SaleOrder.company_id.cust_care_email,SaleOrder.company_id.cust_care_phone)
                            mail_values = {'email_from': 'info@builderbay.com',
                                           'email_to': SaleOrder.partner_id.email,
                                           'subject': "Order Confirmed - %s"%(SaleOrder.name),
                                           'body_html': Message,
                                           'state': 'outgoing'}
                            mail = request.env['mail.mail'].sudo().create(mail_values)
                            mail.sudo().send(True)

                        #Backend team notification: TODO: switch control
                        SPEmail = SaleOrder.sudo().user_id.partner_id.email or SaleOrder.sudo().user_id.login
                        SPMobile = SaleOrder.sudo().user_id.partner_id.mobile
                        if SPEmail:
                            subject = "Quotation Accepted - %s"%(SaleOrder.name)
                            Message = 'Quotation %s has been accepted by customer %s. Please process it at the earliest.' % (SaleOrder.name, SaleOrder.partner_id.name)
                            mail_values = {'email_from': 'info@builderbay.com',
                                           'email_to': SPEmail,
                                           'subject': subject,
                                           'body_html': Message,
                                           'state': 'outgoing'}
                            mail = request.env['mail.mail'].sudo().create(mail_values)
                            mail.sudo().send(True)
                        if SPMobile:
                            Message = 'Quotation %s has been accepted by customer %s. Please process it at the earliest.' % (SaleOrder.name, SaleOrder.partner_id.name)
                            url = "https://cts.myvi.in:8443//ManageSms/api/sms/Createsms/json/apikey=%s" % (
                                SaleOrder.company_id.sms_apikey)
                            headers = {'Authorization': 'Bearer %s' % (SaleOrder.company_id.get_sms_token())}
                            params = {
                                "msisdn": SPMobile,
                                "sms": Message,
                                "unicode": "0",
                                "senderid": SaleOrder.company_id.sms_senderid,
                                "pingbackurl": "https://builderbay.com/pingback/sms"
                            }
                            requests.post(url, params, headers=headers)

            except Exception as E:
                print(E)
        else: return False

    # @http.route(['/shop/bulkcement/<model("product.template"):product>'], type='http', auth="public", website=True)
    # def bs_bulk_cement(self, product, category='', search='', **kwargs):
    #     Transport2site, unloadAtSite = False, False
    #     RejectionReasons = request.env['bs.rejection.reason'].sudo().search([])
    #     SO = request.env['sale.order'].sudo().search([('product_tmpl_id','=',product.id),
    #                                                   ('partner_id','=',request.env.user.partner_id.id),
    #                                                   ('state','not in',['cancel','expire','reject']),
    #                                                   ]).filtered(lambda x: x.date_order.date() == fields.Date.today())
    #     if SO:
    #         SO = SO[0]
    #         unloadAtSite = SO.order_line.filtered(lambda x: x.product_id.id == request.env.ref('builderbay.hamali_charges').id)
    #         Transport2site = SO.order_line.filtered(lambda x: x.product_id.id == request.env.ref('builderbay.transport_charges').id)
    #
    #     PubCatObj = request.env['product.public.category'].sudo()
    #     BrandAttrLine = request.env['product.template.attribute.line'].sudo().search([('product_tmpl_id','=',product.id),
    #                                 ('attribute_id','=',request.env.ref('builderbay.brand_attribute').id)],limit=1)
    #     StandardVals = self._prepare_product_values(product, category, search, **kwargs)
    #     StandardVals.update({'exclude_products': []})
    #     if request.env.ref('builderbay.hamali_charges'):
    #         StandardVals['exclude_products'] += [request.env.ref('builderbay.hamali_charges').id]
    #     if request.env.ref('builderbay.transport_charges'):
    #         StandardVals['exclude_products'] += [request.env.ref('builderbay.transport_charges').id]
    #
    #     StandardVals.update({'brand': BrandAttrLine.value_ids[0] if BrandAttrLine else False,
    #                          'product_rating': product.sudo().rating_get_stats()})
    #     if product.public_categ_ids:
    #         StandardVals.update({'sibling_categs': PubCatObj.search([('parent_id', 'in', product.public_categ_ids[0].mapped('parent_id.id'))]),
    #                              'child_categs': product.public_categ_ids[0].child_id,
    #                              'ecomm_categ':product.public_categ_ids[0],
    #                              'banners': product.public_categ_ids[0].banner_ids if product.public_categ_ids else False,
    #                              'all_brands': PubCatObj.get_brands(eCommCategIDs=[product.public_categ_ids[0].id]),
    #                              'sale_order': SO,
    #                              'transport_charges':Transport2site,
    #                              'hamali_charges':unloadAtSite,
    #                              'add_brands_data': self.get_brands_grades(product),
    #                              'BrandAttrID': request.env.ref('builderbay.brand_attribute').id,
    #                              'so_reject_reasons': RejectionReasons})
    #     return request.render('builderbay.bulk_cement_pdp', StandardVals)

from odoo.addons.sale.controllers.portal import CustomerPortal as SalePortal
from odoo.addons.helpdesk.controllers.portal import CustomerPortal as Helpdesk
from odoo.addons.portal.controllers.portal import CustomerPortal

from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
from odoo.http import request, route
from odoo import http, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.osv.expression import OR, AND
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
import json
import re
import passlib
import datetime
from datetime import datetime
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.modules.module import get_resource_path

#Button control and order status view in /my/orders page
SOStates = {'draft': 'Pending',
            'sent': 'Price Quoted',
            'sale': 'Quotation Accepted',
            'done': 'Order Confirmed',
            'accept': 'Order Accepted',
            'reject': 'Order Rejected',
            'cancel': 'Order Cancelled',
            'paid': 'Paid',
            'process': 'Processing'}



class BSCustomerPortal1(CustomerPortal):
    
    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices', download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual, invoice_sudo.currency_id, country_id)

        return request.render("account.portal_invoice_page", values)

    @http.route('/add/address', type='json', auth="user", sitemap=False, website=True)
    def bs_add_address(self, **kw):
        kw.update({'parent_id':request.env.user.partner_id.id})
        try:
            request.env['res.partner'].sudo().create(kw)
            return kw.get('type')
        except Exception as e:
            return False

    @http.route('/edit/address', type='json', auth="user", sitemap=False, website=True)
    def bs_edit_address(self, **kw):
        AddressID = int(kw.get('address-id'))
        kw.pop('address-id')
        try:
            request.env['res.partner'].sudo().browse(AddressID).write(kw)
            return kw.get('type')
        except Exception as e:
            return False

    @http.route('/modal/address', type='json', auth="user", sitemap=False, website=True)
    def bs_modal_address(self, **kw):
        AddRec = request.env['res.partner'].sudo().browse(int(kw.get('address_id',False)))
        AllStates = request.env['res.country.state'].sudo().search([('country_id.code', '=', 'IN')])
        AllDistricts = request.env['bs.district'].sudo().search([])
        Values = {'address': AddRec, 'type':kw.get('type'), 'state_ids':AllStates, 'district_ids':AllDistricts}
        return request.env['ir.ui.view']._render_template('builderbay.bs_modal_address', Values)

    @route(['/assign/delivery'], auth='user', cors='*', csrf=False, website=True)
    def assign_delivery(self, **kw):
        User = request.env.user
        orders = request.env['bs.delivery.verification'].get_default_assign_value(User)
        return request.render("builderbay.assign_delivery",{'orders':orders})

    @route(['/delivery/verification'], auth='user', cors='*', csrf=False, website=True)
    def delivery_verify(self, **kw):
        User = request.env.user
        picking_id = int(kw['picking_id'])
        default_value = request.env['bs.delivery.verification'].get_default_value(User,picking_id)
        return request.render("builderbay.delivery_verify",default_value)

    @route(['/bs/verified'], auth='public', cors='*', csrf=False, website=True)
    def delivery_verifyed(self, **kw):
        message = 'Succesfully verified'
        v_id = int(kw['code'])
        token = kw['string']
        verify_obj = request.env['bs.delivery.verification'].sudo().browse(v_id)
        if verify_obj.email_token != token:
            message = 'Vrification Failed'
        return request.render("builderbay.delivery_verify_message",{'message':message})

    @route(['/bs/devivery/verification-otp'], auth='public', cors='*', csrf=False, website=True)
    def delivery_verifyed_otp(self, **kw):
        message = 'Succesfully verified'
        v_id = int(kw['vid'])
        otp = kw['otp']
        verify_obj = request.env['bs.delivery.verification'].sudo().browse(v_id)
        if verify_obj.otp != otp:
            message = 'Vrification Failed'
        return request.render("builderbay.delivery_verify_message",{'message':message})

    @route(['/bs/devivery/verification'], auth='user', cors='*', csrf=False)
    def delivery_verify_otp(self, **kw):
        kw['sale_id'] = int(kw['sale_id'])
        kw['partner_id'] = int(kw['partner_id'])
        kw['user_id'] = int(kw['user_id'])
        verify_obj = request.env['bs.delivery.verification'].sudo().create(kw)
        User = request.env['res.users'].sudo().browse(SUPERUSER_ID)
        try:
            emails = list(set([kw['email']]))
            cus_emails = list(set([verify_obj.partner_id.email]))
            verify_obj.send_verification_email(emails)
            verify_obj.send_info_email(cus_emails)
            OTPSent = request.env['res.partner'].send_otp(False, 'login', 'verify',kw['mobile'])
            print(OTPSent)
#             if OTPSent['response']:
            verify_obj.otp = OTPSent['otp']
        except Exception as e:
            pass
        return request.render("builderbay.delivery_verify_otp",{'vid':verify_obj.id})

    @http.route('/change/password', type='json', auth="user", sitemap=False, website=True)
    def portal_change_password(self, **kw):
        CurrentPassword, NewPassword = kw.get('CurrentPassword'), kw.get('NewPassword')
        assert CurrentPassword
        request.env.cr.execute(
            "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
            [request.env.user.id]
        )
        [hashed] = request.env.cr.fetchone()
        valid, replacement = passlib.context.CryptContext(['pbkdf2_sha512', 'plaintext'], deprecated=['plaintext']).verify_and_update(CurrentPassword, hashed)
        if valid: return request.env.user.change_password( CurrentPassword, NewPassword)
        else: return False

    @route(['/read/notification'], type='json', auth='public', sitemap=False, website=True)
    def bs_read_notification(self, **kw):
        if kw.get('notification_id'):
            NotRec = request.env['bs.notification'].sudo().browse(int(kw.get('notification_id')))
            if not NotRec.read:
                NotRec.write({'read': True, 'read_time': datetime.now()})
            return True
        return False


    # Overridden: For My Account
    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        return request.render("builderbay.my_account")

    @route(['/partner/ledger'], type='http', auth='user', website=True)
    def bs_partner_ledger(self, tab='invoice', **kw):

        invoics = []
        partner = request.env.user.partner_id
        accountMove = request.env['account.move'].sudo()
        inv_domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', '=', 'posted'),('invoice_origin','!=',False)
        ]
        date_begin = request.httprequest.args.getlist('from_date')[0] if request.httprequest.args.getlist('from_date') else None
        date_end = request.httprequest.args.getlist('date_end')[0] if request.httprequest.args.getlist('date_end') else None
        if date_begin and date_end:
            inv_domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]
        invoices = accountMove.search(inv_domain, order='invoice_date desc')
        BrandAttrID = request.env.ref('builderbay.brand_attribute').id
        for inv in invoices:
            product = inv.invoice_line_ids.mapped('product_id')
            pro_tmpl = product.mapped('product_tmpl_id')
            Attributes = ', '.join(product.product_template_attribute_value_ids
                       .filtered(lambda x:x.attribute_id.id != BrandAttrID).mapped('name'))
            total_qty = sum(inv.invoice_line_ids.mapped('quantity'))
            invoics.append({
                'pro_tmpl':pro_tmpl[0],
                'origin':inv.invoice_origin,
                'attr':Attributes,
                'total_qty':total_qty,
                'payment_reference':inv.payment_reference,
                'inv_object':inv
            })
        if not tab or tab not in ['invoice', 'ledger']: tab = 'invoice'
        vals = {'tab':tab,
                'invoices':invoics,
                'date': date_begin,
                'date_end':date_end}
        return request.render('builderbay.bs_partner_ledger',vals)
    
    @route(['/contact/address/create'], type='http', auth='user', website=True)
    def address_create(self, **post):
        partner = request.env.user.partner_id
        st = request.env['res.country.state'].sudo().search([('name','=',post.get('state_id'))])
        country = request.env['res.country'].sudo().search([('name','=','India')])
        post['state_id'] = st.id
        post['country_id'] = country.id
        post['parent_id'] = partner.id
        request.env['res.partner'].sudo().create(post)
        return request.redirect('/my/address')
    
    @route(['/order/reset/draft'], type='http', auth='user', website=True)
    def reset_order_draft(self, **post):
        order = request.env['sale.order'].sudo().browse(int(post['order']))
        order.sudo().action_draft()
        return request.redirect('/my/orders')

    @route(['/my/address'], type='http', auth='user', website=True)
    def bs_address(self, tab='invoice',**kw):
        partner = request.env.user.partner_id
        vals = {}
        billing = request.env['res.partner'].search([('parent_id','=',partner.id),('type','=','invoice')])
        delivery = request.env['res.partner'].search([('parent_id','=',partner.id),('type','=','delivery')])

        if not tab or tab not in ['invoice', 'delivery']: tab = 'invoice'

        vals.update({'billing':billing,
                     'delivery':delivery,
                     'partner':partner,
                     'district_ids': request.env['bs.district'].sudo().search([]),
                     'state_ids': request.env['res.country.state'].sudo().search([('country_id.code', '=', 'IN')]),
                     'tab': tab
                     })
        return request.render('builderbay.bs_address',vals)

    @route(['/my/security'], type='http', auth='user', website=True)
    def bs_security(self, **kw):
        user = request.env.user.sudo()
        pas = user.password
        partner = request.env.user.partner_id.sudo()
        vals = {'name':partner.name,'email':user.login,'mobile':partner.mobile,'password':'_______1____'}
        return request.render('builderbay.bs_login_security',vals)

    @route(['/my/refunds'], type='http', auth='user', website=True)
    def bs_refunds(self, tab='refund', **kw):
        partner = request.env.user.partner_id
        ReqArgs = request.httprequest.args
        pickingModel = request.env['stock.picking']
        ticket_types = request.env['helpdesk.ticket.type'].search([('name','ilike','%Refund%')])
        domain = [('partner_id', 'child_of', partner.ids),
                  ('state', '=',  'done')]
        date_begin = ReqArgs.getlist('from_date')[0] if ReqArgs.getlist('from_date') else None
        date_end = ReqArgs.getlist('date_end')[0] if ReqArgs.getlist('date_end') else None
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        returnPicks1 = pickingModel.search(domain).filtered(lambda x: 'Return' in x.origin )
        returnPicks2 = pickingModel.search(domain).filtered(lambda x: 'return' in x.origin )
        returnPicks = returnPicks1 | returnPicks2
        listPicking = []
        BrandAttrID = request.env.ref('builderbay.brand_attribute').id
        for returnPick in returnPicks:
            moves = returnPick.mapped('move_ids_without_package')
            refund_elg_amt = 0
            invoices = returnPick.sale_id.mapped('invoice_ids').filtered(lambda y:y.move_type == 'out_invoice')
            mv_qty = 0
            for move in moves:
                inv_lines = request.env['account.move.line'].search([('move_id','in',invoices.ids),('product_id','=',move.product_id.id)], order="create_date desc")
                for invL in inv_lines:
                    if move.product_uom_qty == invL.quantity:
                        refund_elg_amt = move.product_uom_qty * invL.price_unit
                        break
                    elif move.product_uom_qty < invL.quantity:
                        refund_elg_amt = move.product_uom_qty * invL.price_unit
                        break
                    elif move.product_uom_qty > invL.quantity:
                        if mv_qty == 0:
                            mv_qty = move.product_uom_qty - invL.quantity
                            refund_elg_amt += mv_qty * invL.price_unit
                        else:
                            mv_qty = invL.quantity - mv_qty
                            refund_elg_amt += mv_qty * invL.price_unit
            
            orderLine = returnPick.sale_id.order_line
            amount_total = sum(invoices.mapped('amount_total'))
            inv_name = invoices.mapped('name')
            so_payment = request.env['account.payment'].search([('ref','ilike',returnPick.sale_id.name),('state','=','posted')])
            inv_payment = request.env['account.payment'].search([('ref','in',inv_name),('state','=','posted')])
            payment = so_payment | inv_payment
            amount_paid = sum(payment.mapped('amount'))
            payment_ref = ', '.join(payment.mapped('name'))
            rfn_inv = invoices
            product = orderLine.mapped('product_id')
            pr_tmpl = product.mapped('product_tmpl_id')[0]
            grade = ', '.join(product.product_template_attribute_value_ids.filtered(lambda x:x.attribute_id.id != BrandAttrID).mapped('name'))
            so = returnPick.sale_id
            qty = sum(orderLine.filtered(lambda x:x.product_id.type != 'service').mapped('product_uom_qty'))
#             inv_ref = rfn_inv.name
            amount_untax = sum(rfn_inv.mapped('amount_untaxed'))
            inv_date  = rfn_inv[-1].invoice_date
            amount_tax = sum(rfn_inv.mapped('amount_tax'))
            amt_total = sum(rfn_inv.mapped('amount_total'))
            add_date = returnPick.date_done.strftime('%d %B, %Y')
            dict_pick = {
                'product_template':pr_tmpl,
                'sale_order': so,
                'grade':grade,
                'qty':qty,
                'amount_paid':amount_paid,
                'inv_amount':amount_total,
                'inv_ref':payment_ref,
                'picking':returnPick,
                'addon_date':add_date,
                'amount_untax':amount_untax,
                'inv_date':inv_date,
                'amount_tax':amount_tax,
                'amount_total':amt_total,
                'refund_elg_amt' :refund_elg_amt,
                }
            listPicking.append(dict_pick)
        if not tab or tab not in ['refund','payment']: tab = 'refund'
        return request.render('builderbay.bs_refund',{'pickings':listPicking,
                                                        'bank_ids':partner.bank_ids,
                                                        'ticket_types':ticket_types,
                                                        'date': date_begin,
                                                        'date_end':date_end,
                                                        'tab': tab})

    @route(['/my/shipments'], type='http', auth='user', website=True)
    def bs_shipments(self, **kw):
        Shipments = {}
        Pickings = request.env['stock.picking'].sudo().search([('partner_id','child_of',request.env.user.partner_id.ids),
                                                               ('picking_type_id.sequence_code','=','OUT')])
        print(Pickings)
        for pick in Pickings:
            if pick.status_date_details: status_pick_dates = pick.status_date_details.split('___')
            else: status_pick_dates = []

            Shipments[pick] = {'so': False, 'inv': False, 'image': False, 'product_name': "",
                               'status_pick_dates':status_pick_dates}

            ProductIDs = [line.product_id.id for line in pick.move_ids_without_package]
            print('ProductIDs',ProductIDs)
            SO = request.env['sale.order'].sudo().search([('name','=',pick.origin)], limit=1)
            PO = request.env['purchase.order'].sudo().search([('name','=',pick.origin)], limit=1)
            print('SO,PO',SO, PO)
            if SO:
                Shipments[pick]['so'] = SO
                Invoices = SO.sudo().invoice_ids.filtered(lambda x: [i for i in ProductIDs
                                                              if i in x.invoice_line_ids.mapped('product_id.id')])
                print('Invoices',Invoices)
                if Invoices: Shipments[pick]['inv'] = Invoices

        return request.render('builderbay.bs_track_shipment',{'shipments':Shipments,
                                                                'status':['Preparation', 'Shipped'],
                                                                'state': {'draft': 'Preparation',
                                                                          'waiting': 'Preparation',
                                                                          'confirmed': 'Preparation',
                                                                          'assigned': 'Preparation',
                                                                          'done': 'Shipped',
                                                                          'cancel': 'Cancelled'}})

    @route(['/my/enquiries'], type='http', auth='user', website=True)
    def bs_enquiries(self, tab='click', **kw):
        LeaveEnquiries = request.env['bs.enquiry'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
        ClickUploads = request.env['bs.click.upload'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
        if not tab or tab not in ['enquiry', 'click']: tab = 'click'
        return request.render('builderbay.bs_enquiries', {'enquiries': LeaveEnquiries,
                                                            'clickuploads':ClickUploads,
                                                            'tab': tab})

    @route(['/remove/wish'], type='json', auth='user', sitemap=False, website=True)
    def bs_wish_remove(self, **kw):
        order_id = kw.get('order_id')
        so = request.env['sale.order'].browse(int(order_id))
        so.wishlist = False
        return {'success':True}
    
    @route('/manage/gst', type="http", auth="user", website=True)
    def bs_manage_gst(self, **kw):
        Partner = request.env.user.partner_id
        vals = {'states': request.env['res.country.state'].sudo().search([('country_id.code','=','IN')]), 'gst_recs':False}
        if Partner.parent_id:
            if Partner.parent_id.vat: vals.update({'gst_recs': Partner.parent_id})
        else:
            if Partner.company_type == 'company' and Partner.vat: vals.update({'gst_recs': Partner})
        return request.render('builderbay.bs_manage_gst', vals)

    @route('/bs/enquiry', type="http", auth="user", website=True)
    def bs_leave_enquiry(self, **kw):
        Partner = request.env.user.partner_id
        States = request.env['res.country.state'].sudo().search([('country_id.code','=','IN')])
        Categories = request.env['product.public.category'].sudo().search([('parent_id', '=', False),
                                                                           ('customer_type','in',[Partner.customer_type, 'both'])])
        Subcategories = request.env['product.public.category'].sudo().search([('parent_id', '!=', False),
                                                                              ('customer_type','in',[Partner.customer_type, 'both'])])
        Brands = request.env['product.attribute.value'].sudo().search(
                            [('attribute_id', '=', request.env.ref('builderbay.brand_attribute').id),
                             ('customer_type', 'in', [Partner.customer_type, 'both'])])
        UOM = request.env['uom.uom'].sudo().search([])
        values = {'states': States,
                  'categories': Categories,
                  'subcategories': Subcategories,
                  'brands': Brands,
                  'uoms': UOM}
        return request.render('builderbay.bs_enquiry',values)

    @http.route('/create/enquiry', type='json', auth="user", sitemap=False, website=True)
    def create_bs_enquiry(self, **kw):
        if kw.get('type') == 'PriceEnquiry':
            kw.pop('type')
            FinalVals = {}
            for i in kw:
                if type(kw[i]) == list: FinalVals[i] = [(6, 0, list(map(int,kw[i])))]
                else: FinalVals[i] = kw[i]
            EnqID = request.env['bs.enquiry'].sudo().create(FinalVals)
            return True if EnqID else False

        elif kw.get('type') == 'ClickUpload':
            EnquiryIDs = []
            DeliveryIDs = []
            for attach in kw.get('documents'):
                EnquiryIDs += [request.env['ir.attachment'].sudo().create({'type': 'binary', 'name': attach,
                                 'datas': kw.get('documents').get(attach).split(';base64,')[-1]}).id]
            for attach in kw.get('delivery'):
                DeliveryIDs += [request.env['ir.attachment'].sudo().create({'type': 'binary', 'name': attach,
                                'datas': kw.get('delivery').get(attach).split(';base64,')[-1]}).id]

            ClickUpload = request.env['bs.click.upload'].sudo().create(
                            {'price_enquiry_attachment_ids': [(6, 0, EnquiryIDs)],
                             'delivery_address_attachment_ids': [(6, 0, DeliveryIDs)],
                             'name': kw.get('name',"").strip(),
                             'phone_no': kw.get('phone',"").strip(),
                             'gstin': kw.get('gstin').strip() if kw.get('gstin') else '',
                             'partner_id': request.env.user.partner_id.id,
                             'trade_name': kw.get('trade_name').strip() if kw.get('trade_name') else '',
                             'address': kw.get('address').strip()})
            return True if ClickUpload else False

        else:
            return False

    @http.route('/bank/add', type='json', auth="user", sitemap=False, website=True)
    def bs_add_bank(self, **kw):

        BankID = request.env['res.bank'].sudo().search([('name','=',kw.get('bank_name'))], limit=1)
        if not BankID: BankID = request.env['res.bank'].sudo().create({'name': kw.get('bank_name')})

        BankAttachmentID = request.env['ir.attachment'].sudo().create({'type': 'binary',
                                                          'name': kw.get('bank_attachment_name'),
                                                          'datas': kw.get('bank_attachment_base64')})

        CreatedBankID = request.env['res.partner.bank'].sudo().create({'partner_id': request.env.user.partner_id.id,
                                                                        'acc_holder_name': request.env.user.partner_id.name,
                                                                        'acc_number': kw.get('acc_number'),
                                                                        'is_default': kw.get('is_default'),
                                                                        'bank_id': BankID.id if BankID else False,
                                                                        'currency_id': request.env.company.currency_id.id,
                                                                        'company_id': request.env.company.id,
                                                                        'ifsc_code': kw.get('ifsc_code'),
                                                                        'bank_address': kw.get('bank_address'),
                                                                        'bank_attachment_id': BankAttachmentID.id if BankAttachmentID else False,
                                                                        })
        if kw.get('is_default') and CreatedBankID:
            request.env['res.partner.bank'].sudo().search([('id','!=',CreatedBankID.id)]).write({'is_default':False})
        return True

    @http.route('/gst/add', type='json', auth="user", sitemap=False, website=True)
    def bs_add_gst(self, **kw):
        GSTRec = request.env['bs.gst'].sudo().search([('name','=',kw.get('gstin'))],limit=1)
        GSTRec.write({'partner_id': request.env.user.partner_id.id})
        if not GSTRec.mobile: GSTRec.write({'mobile': kw.get('gst_mobile')})
        if not GSTRec.city: GSTRec.write({'city': kw.get('gst_city')})
        if not GSTRec.state_id: GSTRec.write({'state_id': kw.get('gst_state_id')})
        if not GSTRec.pincode: GSTRec.write({'pincode': kw.get('gst_zip')})
        if not GSTRec.trade_name: GSTRec.write({'trade_name': kw.get('shop_name')})
        if not GSTRec.legal_name: GSTRec.write({'legal_name': kw.get('legal_name')})
        return True

    @http.route('/gst/edit', type='json', auth="user", sitemap=False, website=True)
    def bs_edit_gst(self, **kw):
        GSTRec = request.env['bs.gst'].sudo().browse(int(kw.get('gst_id',False)))
        return request.env['ir.ui.view']._render_template('builderbay.gst_modal', values={'gst_id':GSTRec,
                                                                                            'states': request.env['res.country.state'].sudo().search([('country_id.code','=','IN')])}),

class BSHelpdesk(Helpdesk):
    

    @route(['/support/ticket/create'], type='http', auth='user', website=True)
    def ticket_create(self, **post):
        partner = request.env.user.partner_id
        post['partner_id'] = partner.id
        post['team_id'] = 1
        post['partner_email'] = partner.email
        if post.get('sale_order_id'):
            if post['sale_order_id'].isdigit():
                post['sale_order_id'] = int(post['sale_order_id'])
                order = request.env['sale.order'].sudo().browse(int(post['sale_order_id']))
                order.sudo().refund_ticket = True
            else:
                post.pop('sale_order_id') #non mandatory
        post['ticket_type_id'] = int(post['ticket_type_id'])
        request.env['helpdesk.ticket'].sudo().create(post)
        return request.redirect('/my/tickets')
    
    # Overridden: For My Account
    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None,
                            groupby='none', search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order'].sudo()
        so_domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])
        ]
        orders = SaleOrder.search(so_domain)
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
            'reference': {'label': _('Reference'), 'order': 'id'},
            'update': {'label': _('Last Stage Update'), 'order': 'date_last_stage_update desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'assigned': {'label': _('Assigned'), 'domain': [('user_id', '!=', False)]},
            'unassigned': {'label': _('Unassigned'), 'domain': [('user_id', '=', False)]},
            'open': {'label': _('Open'), 'domain': [('close_date', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('close_date', '!=', False)]},
            'last_message_sup': {'label': _('Last message is from support')},
            'last_message_cust': {'label': _('Last message is from customer')},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'id': {'input': 'id', 'label': _('Search in Reference')},
            'status': {'input': 'status', 'label': _('Search in Stage')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'stage': {'input': 'stage_id', 'label': _('Stage')},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if filterby in ['last_message_sup', 'last_message_cust']:
            discussion_subtype_id = request.env.ref('mail.mt_comment').id
            messages = request.env['mail.message'].search_read(
                [('model', '=', 'helpdesk.ticket'), ('subtype_id', '=', discussion_subtype_id)],
                fields=['res_id', 'author_id'], order='date desc')
            last_author_dict = {}
            for message in messages:
                if message['res_id'] not in last_author_dict:
                    last_author_dict[message['res_id']] = message['author_id'][0]

            ticket_author_list = request.env['helpdesk.ticket'].search_read(fields=['id', 'partner_id'])
            ticket_author_dict = dict(
                [(ticket_author['id'], ticket_author['partner_id'][0] if ticket_author['partner_id'] else False) for
                 ticket_author in ticket_author_list])

            last_message_cust = []
            last_message_sup = []
            for ticket_id in last_author_dict.keys():
                if last_author_dict[ticket_id] == ticket_author_dict[ticket_id]:
                    last_message_cust.append(ticket_id)
                else:
                    last_message_sup.append(ticket_id)

            if filterby == 'last_message_cust':
                domain = [('id', 'in', last_message_cust)]
            else:
                domain = [('id', 'in', last_message_sup)]

        else:
            domain = searchbar_filters[filterby]['domain']
        if request.env.user.has_group('base.group_portal'):
            domain += [('partner_id','=',request.env.user.partner_id.id)]
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('id', 'all'):
                search_domain = OR([search_domain, [('id', 'ilike', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                discussion_subtype_id = request.env.ref('mail.mt_comment').id
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search),
                                                    ('message_ids.subtype_id', '=', discussion_subtype_id)]])
            if search_in in ('status', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            domain += search_domain

        # pager
        tickets_count = len(request.env['helpdesk.ticket'].search(domain))
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in,
                      'search': search},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        tickets = request.env['helpdesk.ticket'].sudo().search(domain, order=order, limit=self._items_per_page,
                                                        offset=pager['offset'])
        request.session['my_tickets_history'] = tickets.ids[:100]

        ticket_types = request.env['helpdesk.ticket.type'].search([])
        if groupby == 'stage':
            HelpDeskTicket = [request.env['helpdesk.ticket'].sudo().concat(*g) for k, g in
                               groupbyelem(tickets, itemgetter('stage_id'))]
        else:
            HelpDeskTicket = [tickets]

        values.update({
            'date': date_begin,
            'helpdesk_tickets': HelpDeskTicket,
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'ticket_types':ticket_types,
            'orders':orders,
            'BrandAttrID': request.env.ref('builderbay.brand_attribute').id,
        })
        return request.render("builderbay.bs_support_tickets", values)


class BSWishlist(WebsiteSaleWishlist):

    # Overridden: for My account: TODO:check for public
    @http.route(['/shop/wishlist'], type='http', auth="user", website=True, sitemap=False)
    def get_wishlist(self, count=False, **kw):

        whLst = []
        domain = [('partner_id', '=', request.env.user.partner_id.id)]
        SOLines = request.env['sale.order'].with_user(request.env.user).search(domain + [('state','in',('draft','sale','accept')),('show_in_cart','=',False)],
                                                          order= 'create_date desc').mapped('order_line')

        for wish in request.env['customer.wishlist'].sudo().search(domain+[('state','=','open')], order='create_date desc'):
            if wish.order_id:
                if wish.order_id.state == 'sent':
                    whLst.append([wish, wish.order_id, wish.order_id])
                else:
                    whLst.append([wish, False, wish.order_id])
            else:
                whLst.append([wish,False,False])
        return request.render("builderbay.bs_wishlist", dict(wishes=whLst))

class BSSale(SalePortal):

    # Overridden: Vendor
    @http.route(['/bs/orders'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sale', 'done'])
        ]

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager
        orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_orders_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'order',
            'pager': pager,
            'default_url': '/my/orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("builderbay.bs_orders", values)



    # My account - customer orders
    @http.route('/my/orders', type='http', auth="user", website=True, csrf=False)
    def bs_my_orders(self, page=1, sortby=None, tab='all', **kw):
        state_list = ['sent','sale', 'done','draft','reject','accept','cancel']
        date_begin = request.httprequest.args.getlist('from_date')[0] if request.httprequest.args.getlist('from_date') else None
        date_end = request.httprequest.args.getlist('date_end')[0] if request.httprequest.args.getlist('date_end') else None
        tab = request.httprequest.args.getlist('tab')[0] if request.httprequest.args.getlist('tab') else None
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order'].sudo()
        BrandAttrID = request.env.ref('builderbay.brand_attribute').id

        if not tab or tab not in ['all', 'rejected', 'cancel']: tab = 'all'
        
        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', state_list)
        ]
        
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        # count for pager

        order_count = SaleOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        
        # content according to pager
        domain = OR([domain, [('partner_id','=',partner.id)]])
        if date_begin and date_end:
            domain = AND([domain, [('date_order', '>=', date_begin),('date_order', '<=', date_end)]])
        orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_orders_history'] = orders.ids[:100]

        PortalVals = {'all':[], 'cancelled':[], 'rejected':[]}
        print(len(orders), domain)
        for ord in orders:

            ProductTemplates = list(set(ord.order_line.filtered(lambda x: x.product_id.type == 'product').mapped('product_id.product_tmpl_id')))
            if len(ProductTemplates) == 1:
                ProdImage = ProductTemplates[0].mapped('image_1024')[0] if ProductTemplates[0].mapped('image_1024') else False
            else: ProdImage = False

            ProdDetails, ProdName = "", ""
            ValidProds = ord.order_line.filtered(lambda x: x.product_id.type == 'product')
            for line in ValidProds:
                ProdName += line.product_id.name + '\n'
                # ProdDetails += line.name + " - " + str(line.product_uom_qty) + line.product_uom.name + '\n'

            StatusColor = 'badge-info' #TODO
            if ord.state == 'cancel':
                PortalVals['cancelled'] += [{'id':ord.id, 'image':ProdImage, 'ref': ord.name, 'prods':ValidProds,
                                            'product_name': ProdName, 'SO':ord, 'attributes':ProdDetails,
                                             'date': ord.create_date, 'status': SOStates.get(ord.state)}]

            elif ord.state == 'reject':
                PortalVals['rejected'] += [{'id': ord.id, 'image': ProdImage, 'ref': ord.name, 'product_name': ProdName,
                                            'reject_info': ord.rejection_info,'prods':ValidProds,
                                            'reject_reason': ord.rejection_reason, 'SO': ord,
                                            'attributes': ProdDetails, 'date': ord.create_date,
                                            'status': SOStates.get(ord.state)}]
            else:
                PortalVals['all'] += [{'id': ord.id, 'image': ProdImage, 'ref': ord.name, 'product_name': ProdName,
                                       'attributes': ProdDetails, 'date': ord.create_date,'prods':ValidProds,
                                       'status': SOStates.get(ord.state),'SO':ord,
                                       'placed_by': ord.user_id.name, 'amount': ord.amount_total,
                                       'inv_ids': ord.mapped('invoice_ids').filtered(lambda x: x.authorized_by),
                                       'billed_to': ord.partner_invoice_id.name,
                                       'shipped_to': ord.partner_shipping_id.name,
                                       'pickings': ord.mapped('picking_ids'), 'show_in_cart': ord.show_in_cart}]

            # TODO:check for multiple products;
            #if single prod temp -- else default image
            # orderlines -- attrs and qty in each line

            # if ord.order_line:
            #     SO = ord.order_line.filtered(lambda x: x.product_id.type == 'product')
            #     ProdImage = SO.mapped('product_id.product_tmpl_id.image_1024')[0] if SO.mapped('product_id.product_tmpl_id.image_1024') else False
            #     ProdName = ', '.join(SO.mapped('product_id.product_tmpl_id.name'))
            #     Attributes = ', '.join(SO.mapped('product_id.product_template_attribute_value_ids').filtered(lambda x: x.attribute_id.id != BrandAttrID).mapped('name'))
            #     Qty = sum(SO.mapped('product_uom_qty'))
            #     UOM = ', '.join(SO.mapped('product_uom.name'))
            #
            #     if ord.state == 'cancel':
            #         PortalVals['cancelled'] += [{'id':ord.id, 'image':ProdImage, 'ref': ord.name, 'product_name': ProdName,
            #     'qty': Qty,'SO':ord, 'attributes':Attributes, 'uom': UOM, 'date': ord.create_date, 'status': ord.state}]
            #
            #     elif ord.state == 'reject':
            #         PortalVals['rejected'] += [{'id':ord.id, 'image':ProdImage, 'ref': ord.name, 'product_name': ProdName,
            #                 'qty': Qty,'reject_info':ord.rejection_info, 'reject_reason':ord.rejection_reason,'SO':ord,
            #                         'attributes':Attributes, 'uom': UOM, 'date': ord.create_date, 'status': ord.state}]
            #
            #     else:
            #         print('else block',ord.state, ord.name)
            #         PortalVals['all'] += [{'id': ord.id, 'image': ProdImage, 'ref': ord.name, 'product_name': ProdName,
            #                                'attributes': Attributes, 'uom': UOM, 'date': ord.create_date,
            #                                'status': ord.state, 'qty': Qty,
            #                                'placed_by': ord.user_id.name, 'amount': ord.amount_total,
            #                                'inv_ids': ord.mapped('invoice_ids'),
            #                                'billed_to': ord.partner_invoice_id.name,
            #                                'shipped_to': ord.partner_shipping_id.name,
            #                                'pickings': ord.mapped('picking_ids'), 'show_in_cart': ord.show_in_cart}]

        values.update({
            'date': date_begin,
            'date_end':date_end,
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'default_url': '/my/orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'tab':tab,
            'portal_vals':PortalVals,
            'BrandAttrID': BrandAttrID,
        })
        return request.render("builderbay.bs_my_orders",values)

    @http.route('/my/banks', type='http', auth="user", website=True, csrf=False)
    def bs_my_banks(self, tab="bs", *kw):
        PartnerRec = request.env.user.partner_id
        if not tab or tab not in ['bs', 'others']: tab = 'bs'
        vals = {'other_banks': PartnerRec.bank_ids, 'bs_bank': {}, 'tab': tab}
        if PartnerRec.bs_acct_no:
            vals.update({'bs_bank': {'bs_bnf_name': PartnerRec.bs_acct_beneficiary_name,
                                     'bs_acct_no': PartnerRec.bs_acct_no,
                                     'bs_bank': PartnerRec.bs_acct_bank_id.name,
                                     'bs_ifsc': PartnerRec.bs_acct_ifsc_code,
                                     'bs_bank_address': PartnerRec.bs_acct_address,
                                     'tab': tab}})
        return request.render("builderbay.bs_profile_banks", vals)
    
from odoo import api, fields, models, _
import datetime
from datetime import datetime


class BSRfq(models.Model):
    _name = "bs.rfq"
    _description = "Request For Quote"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Order Reference', required=True, index=True, copy=False, default='New')
    origin = fields.Char('Source Document', copy=False,
        help="Reference of the document that generated this RFQ "
             "request (e.g. a sales order)")
    so_id = fields.Many2one('sale.order', string='Sale Order')
    po_id = fields.Many2one('purchase.order', string="Purchase Order")
    date_order = fields.Datetime('Order Date', related="so_id.date_order")
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, auto_join=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    dest_address_id = fields.Many2one('res.partner', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string='Customer Address')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('accept', 'Vendor Accepted'),
        ('updated', 'Prices Updated'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected'),
        ('confirm', 'Prices Confirmed'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    order_line = fields.One2many('bs.rfq.order.line', 'rfq_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)],
                                         'done': [('readonly', True)]}, copy=True)

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_bs_tax = fields.Monetary(string='BS Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
        default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id)

    notes = fields.Text(string="Terms & Conditions")
    supplier_info_id = fields.Many2one('product.supplierinfo',string="Supplier Info")
    

    @api.depends('order_line.price_total','order_line.price_subtotal','order_line.taxes_id','order_line.price_unit')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            bs_percentage = self.env['ir.config_parameter'].sudo().search([('key','=','bs_percentage')])
            amount_total = amount_untaxed + amount_tax
            amount_bs_tax = ((amount_total / 100) * int(bs_percentage.value))
            order.amount_bs_tax = amount_bs_tax
            amount_total = amount_total + order.amount_bs_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_total,
            })

    def accept_rfq(self):
        for rec in self:
            if not rec.state == 'accept': rec.state = 'accept'

    def cancel_rfq(self):
        for rec in self:
            if not rec.state == 'cancel': rec.state = 'cancel'

    def reject_rfq(self):
        for rec in self:
            if not rec.state == 'reject': rec.state = 'reject'

    def confirm_rfq(self):
        ''' Once the prices of RFQ are confirmed, a PO will be raised to that respective vendor.
            Other RFQs will be automatically rejected.
        '''
        for rec in self:
            if not rec.state == 'confirm':
                PoVals = {'vendor_id': rec.vendor_id, 'origin': rec.origin, 'supplier_info_id':rec.supplier_info_id}
                for line in rec.order_line:
                    PoVals[line.product_id.id] = {'product_id': line.product_id.id,
                                                    'name': line.name,
                                                   'product_qty': line.product_qty,
                                                   'product_uom': line.product_uom.id,
                                                   'price_unit': line.price_unit,
                                                   'price_subtotal': line.price_subtotal,
                                                   'date_planned':datetime.now(),
                                                  'taxes_id': line.taxes_id.ids}
                    self.env['sale.order.line'].search([('order_id','=',rec.so_id.id),
                                                        ('product_id','=',line.product_id.id)], limit=1).\
                        write({'price_unit': line.price_unit,
                               'product_uom_qty': line.product_qty,
                               'tax_id': line.taxes_id.ids})

                rec.so_id.with_context({'bs_vendor_info': PoVals}).action_confirm()
                rec.state = 'confirm'
                rec.so_id.rfq_id = rec.id

    #rfq price update
    def getRfqDetails(self, rfq_id):
        html = ''
        rfq = self.browse(rfq_id)
        line_qty = str(sum(rfq.order_line.mapped('product_qty'))) 
        base_price = str(sum(rfq.order_line.mapped('price_unit')))
        tax_total = 0.0
        total = str(rfq.amount_total)
        for index,line in enumerate(rfq.order_line):
            qty = """<input type="text" class="form-control bs-panel-size100" value='"""+str(line.product_qty)+"""'/>"""
            price = """<input type="text" class="form-control bs-panel-size100 v_price" value='"""+str(line.price_unit)+"""'/>"""
            sbu_price = """<input type="text" class="form-control bs-panel-size100 sub_price" value='"""+str(line.price_tax)+"""'/>"""
            total_price = """<input type="text" class="form-control bs-panel-size100 t_price" value='"""+str(line.price_total)+"""'/>"""
            tax = ''
            if len(line.taxes_id) == 1:
                tax = line.taxes_id.name
            elif len(line.taxes_id) > 1:
                taxes = line.taxes_id.mapped('name')
                tax = ','.join(taxes)
            all_taxes = self.env['account.tax'].sudo().search([('id','>',0)])
            tax_html = ''
            tax_total = tax_total + line.price_tax			
            for tax in all_taxes:
                select_text = ''
                if len(line.taxes_id) > 0:
                    if tax.id == line.taxes_id[0].id:
                        select_text = 'selected'
                    else:
                        select_text = ''
                tax_html += '<option value='+str(tax.id)+' '+select_text+'>'+tax.name+'</option>'
            tax_select_html = '<select class="form-control bs-panel-size100 t_tax">'+tax_html+'</select>'
            html += """ <tr class="rf_line">
							<td>"""+str(index+1)+"""<span class="line_id" style="display:none;">"""+str(line.id)+"""</span></td>
							<td class="bs-white-space">"""+str(line.product_id.name)+"""</td>
							<td class="bs-white-space">"""+str(line.product_id.mapped('product_template_attribute_value_ids').name)+"""</td>
							<td>550</td>
							<td>
								"""+qty+"""
							</td>
							<td><span>"""+line.product_uom.name+"""</span></td>
							<td>
								<input type="text" class="form-control bs-panel-size100 t_description" value='"""+str(line.name)+"""'/>
							</td>
							<td>
								"""+price+"""
							</td>
							<td>"""+tax_select_html+"""</td>
							<td>
								"""+sbu_price+"""
							</td>
							<td class="latobold">"""+total_price+"""</td>
						</tr>"""
		
        return html,line_qty,base_price,total,tax_total

    @api.model
    def update_price(self, line_id, price, tax, name):
        rfq_line = self.env['bs.rfq.order.line'].sudo().browse(int(line_id))
        rfq_line.price_unit = price
        rfq_line.name = name
        rfq_line.taxes_id = [(6,0, [int(tax)])]
        rfq_line = self.env['bs.rfq.order.line'].sudo().browse(int(line_id))
        qty = str(sum(rfq_line.rfq_id.order_line.mapped('product_qty')))+ ' ' + rfq_line.product_uom.name
        base_price = str(sum(rfq_line.rfq_id.order_line.mapped('price_unit')))
        total_tax = str(sum(rfq_line.rfq_id.order_line.mapped('price_tax')))
        total = str(rfq_line.rfq_id.amount_total)
        vals = {
            'price_sub':rfq_line.price_subtotal,
            'price_total':rfq_line.price_total,
            'price_tax':rfq_line.price_tax,
            'total_qty':qty,
            'total_bprice':base_price,
            'rf_total':total,
            'taxes_id': int(tax),
            'tax_total': total_tax,
			'line_desc': rfq_line.name
        }
        
        return vals


class BSRFQOrderLine(models.Model):
    _name = 'bs.rfq.order.line'
    _description = 'RFQ Order Line'
    _order = 'rfq_id, sequence, id'

    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    # product_uom_qty = fields.Float(string='Total Quantity')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    # discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)

    rfq_id = fields.Many2one('bs.rfq', string='RFQ Reference', index=True, required=True, ondelete='cascade')
    state = fields.Selection(related='rfq_id.state', store=True, readonly=False)

    partner_id = fields.Many2one('res.partner', related='rfq_id.partner_id', string='Partner', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', 'Currency', related='rfq_id.currency_id')
    company_id = fields.Many2one('res.company', 'Company',  related='rfq_id.company_id')


    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.rfq_id.currency_id,
            'product_qty': self.product_qty,
            'product': self.product_id,
            'partner': self.rfq_id.partner_id,
        }

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

"""class BSConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
	
    bs_percentage = fields.Float('builderbay Percentage')"""
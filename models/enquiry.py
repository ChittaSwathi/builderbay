from odoo import api, fields, models, _


class BSAttachment(models.Model):

    _inherit = "ir.attachment"
    enq_attachment_id = fields.Many2one('bs.click.upload')
    del_attachment_id = fields.Many2one('bs.click.upload')

class BSClickUpload(models.Model):
    _name = 'bs.click.upload'
    _rec_name = 'enq_code'
    _order = 'enq_code desc'

    def get_so_id(self):
        # Returns Sale orders mapped with this enquiry
        if self:
            self.ensure_one()
            AttachedSO = self.env['sale.order'].search([('click_upload_id', '=', self.id)])
            return AttachedSO or False
        return False

    #TODO: remove --- adding multi fields--append data to newer fields
    price_enquiry_attachment_id = fields.Many2one('ir.attachment', string="Price Enquiry")
    delivery_address_attachment_id = fields.Many2one('ir.attachment', string="Delivery Address")

    price_enquiry_attachment_ids = fields.One2many('ir.attachment','enq_attachment_id', string="Price Enquiries")
    delivery_address_attachment_ids = fields.One2many('ir.attachment', 'del_attachment_id', string="Delivery Addresses")

    # Contact Person Details
    enq_code = fields.Char('Sequence', copy=False)
    name = fields.Char(string="Contact Person Name")
    partner_id = fields.Many2one('res.partner', string="Customer")
    phone_no = fields.Char(string="Phone Number")
    gstin = fields.Char(string="GSTIN")
    trade_name = fields.Char(string="Company/Trade Name")
    address = fields.Text(string="Address")
    so_id = fields.Many2one('sale.order', 'Sale Order') #TODO:remove

    @api.model
    def create(self, vals):
        Enq = super(BSClickUpload, self).create(vals)
        Enq.enq_code = self.env['ir.sequence'].next_by_code('bs.click.upload.code')
        return Enq

    def write(self, vals):
        res = super(BSClickUpload, self).write(vals)
        if not self.enq_code: self.env['ir.sequence'].next_by_code('bs.click.upload.code')
        return res


class BSEnquiry(models.Model):
    _name = 'bs.enquiry'
    _rec_name = 'name'
    _order = 'id desc'

    def get_so_id(self):
        #Returns Sale orders mapped with this enquiry
        if self:
            self.ensure_one()
            AttachedSO = self.env['sale.order'].search([('price_enq_id','=',self.id)])
            return AttachedSO or False
        return False

    name = fields.Char('Sequence')
    ecomm_category_ids = fields.One2many('product.public.category', 'upload_enq1_id', string="Category")
    ecomm_subcateg_ids = fields.One2many('product.public.category', 'upload_enq2_id', string="SubCategory")
    brand_ids = fields.One2many('product.attribute.value', 'enquiry_id', string="Brands")
    material_description = fields.Text(string='Material Description')
    uom_id = fields.Many2one('uom.uom', string="Material Units")
    location_ids = fields.One2many('res.country.state', 'upload_enquiry_id', string='Locations')
    partner_id = fields.Many2one('res.partner', string="Customer")
    so_id = fields.Many2one('sale.order', 'Sale Order')#TODO:remove
    quantity = fields.Char('Quantity')

    @api.model
    def create(self, vals):
        Enq = super(BSEnquiry, self).create(vals)
        Enq.name = self.env['ir.sequence'].next_by_code('bs.price.enq.code')
        return Enq

    def write(self, vals):
        res = super(BSEnquiry, self).write(vals)
        if not self.name: self.env['ir.sequence'].next_by_code('bs.price.enq.code')
        return res
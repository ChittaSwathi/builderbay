from odoo import api, fields, models, _
import itertools, logging
_logger = logging.getLogger(__name__)
from odoo.addons.http_routing.models.ir_http import slug

class BSProductTemplate(models.Model):

    _inherit = "product.template"
    attribute_line2_ids = fields.One2many('product.template.attribute.line',
                                          'product_tmpl2_id', 'Product Attributes',
                                          help="Attributes but not variants")

    t_and_c = fields.Html(string='Terms & Conditions')
    conv_uom_ids = fields.Many2many('uom.uom','bs_prod_uom_ids','prod_id','uom_id', string="Conversion UOMs", copy=False)
    moq = fields.Float(string="MOQ")

    is_hot_deal = fields.Boolean(string="Is Hot Deal ?")
    hot_deal_percent = fields.Integer(string="Hot Deal Percentage")
    hot_deal_image = fields.Image("Hot Deal Image", max_width=128, max_height=128, help="This image will be displayed in homepage if product is under hot deals.")

    is_best_selling = fields.Boolean(string="Is Best Selling ?")
    show_adds = fields.Boolean("Show Adds ?", copy=False, default=True)
    is_bulk_cement = fields.Boolean(string="Is Bulk Cement ?")
    customer_type = fields.Selection([('b2b', 'B2B'),
                                      ('b2c', 'B2C'),
                                      ('both', 'Both')], string='Customer Type', default="both")

    web_display_seq = fields.Integer('Website Display Sequence')
    
    
    def get_default_url(self, default_attr):
        """product variant imange fetch from S3 bucket """
        
        final_uri_preview = "/web/static/src/img/placeholder.png"
        try:
            from werkzeug import urls
            import requests
            import re
            s3 = ['shop']
            
            Website_env = self.env['website']
            website = Website_env.get_current_website()
            cdn_url = website.cdn_url
            if not cdn_url:
                return final_uri_preview
            Brands = self.attribute_line_ids.filtered(lambda x: x.attribute_id.id == self.env.ref('builderbay.brand_attribute').id).mapped('value_ids')
            
            if not default_attr:
                public_categ= self.public_categ_ids
                last_cate = "/".join(public_categ.parents_and_self.mapped('name'))
                last_categ=last_cate.replace(" & ","_")
                if last_categ:s3.append(last_categ)
                if Brands:
                    s3.append(Brands.name)
                    if self._context.get('homepage', False):
                        s3.append(Brands.name)
                uri = '/'.join(s3)
                final_uri = urls.url_join(cdn_url, uri)
                response = requests.get(final_uri)
                if response.status_code != 200:
                    final_uri = final_uri_preview
            AttributeIDs = default_attr
            ProdTemplObj = self
            Attributes = len(ProdTemplObj.attribute_line_ids.mapped('attribute_id.id'))
            ProdVariants = ProdTemplObj.product_variant_ids
    
            Combs = []
            for i in itertools.combinations(AttributeIDs, Attributes):
                i = set(i)
                if len(i)==Attributes and i not in Combs: Combs += [i]
    
            ToDisplayProds = ProdVariants.filtered(lambda x: set(x.product_template_attribute_value_ids.mapped('product_attribute_value_id.id')) in Combs)
            
            public_categ = ToDisplayProds[0].public_categ_ids
            last_cate = "/".join(public_categ.parents_and_self.mapped('name'))
            last_categ=last_cate.replace(" & ","_")
            s3.append(last_categ)
            
    #         ProdTemplObj = self.product_tmpl_id
            Brands = self.attribute_line_ids.filtered(lambda x: x.attribute_id.id == self.env.ref('builderbay.brand_attribute').id).mapped('value_ids')
            
            if ToDisplayProds[0].default_code:
                s3.append(Brands.name)
                s3.append(ToDisplayProds[0].default_code)
            else:
                s3.append(Brands.name)
                s3.append(Brands.name)
            
            uri = '/'.join(s3)
            final_uri = urls.url_join(cdn_url, uri)
            _logger.info('FINAL URL -- %s'%(final_uri))
    
            response = requests.get(final_uri)
            if response.status_code != 200:
                if ToDisplayProds[0].default_code:
                    s3 = s3[:-1]
                    s3.append(Brands.name)
                    uri = '/'.join(s3)
                    final_uri = urls.url_join(cdn_url, uri)
                    _logger.info('FINAL URL2 -- %s'%(final_uri))
                    response = requests.get(final_uri)
                    if response.status_code != 200:
                        final_uri = final_uri_preview
#             final_uri = final_uri_preview
        except:
            final_uri = final_uri_preview
        return final_uri
    
    
    
    # def create(self, vals):
    #     res = super(BSProductTemplate, self).create(vals)
    #     print('product.template create', vals, self._context)
    #     if res.product_variant_ids: res.l10n_in_hsn_code = ""
    #     return res
    #
    # def write(self, vals):
    #     res = super(BSProductTemplate, self).write(vals)
    #     if self.product_variant_ids: self.l10n_in_hsn_code = ""
    #     return res


class BSProductProduct(models.Model):

    _inherit = "product.product"
    
    @api.depends('product_template_attribute_value_ids','default_code')
    def _compute_sku_reference(self):
        for prod in self:
            vals = {'sku_reference':'','sku_attr_reference':''}
            attr_produt_value = 'BS-'
            if not prod.default_code: 
                pro_sku = self.env['ir.sequence'].next_by_code('product.sku.code')
                vals.update({'default_code': pro_sku})
            if prod.product_template_attribute_value_ids:
                for attr_val in prod.product_template_attribute_value_ids:
                    if not attr_produt_value and attr_val.product_attribute_value_id.sku_code:
                        attr_produt_value = attr_val.product_attribute_value_id.sku_code
                    else:
                        if attr_val.product_attribute_value_id.sku_code:
                            attr_produt_value += '-'+attr_val.product_attribute_value_id.sku_code
                    
                vals.update({
                    'sku_reference': attr_produt_value,
                    'sku_attr_reference':attr_produt_value,
                })
            prod.update(vals)
            

    l10n_in_hsn_code = fields.Char(string="HSN Code", copy=False)
    sku_reference = fields.Char(string="SKU Reference", copy=False, help="SKU reference", compute = '_compute_sku_reference')
    sku_attr_reference = fields.Char(string="SKU Reference", copy=False, help="SKU reference")

    # def create(self, vals):
    #     res = super(BSProductProduct, self).create(vals)
    #     print('product.product create', vals, self._context, vals['product_tmpl_id'])
    #     if vals.get('l10n_in_hsn_code') and res.product_tmpl_id.l10n_in_hsn_code:
    #         res.product_tmpl_id.l10n_in_hsn_code = ""
    #     return res
    #
    # def write(self, vals):
    #     res = super(BSProductProduct, self).write(vals)
    #     print('product.product write', vals, self, self._context, self.product_tmpl_id)
    #     if vals.get('l10n_in_hsn_code') and self.product_tmpl_id.l10n_in_hsn_code:
    #         self.product_tmpl_id.l10n_in_hsn_code = ""
    #     return res


class BSProductAttribute(models.Model):

    _inherit = "product.attribute"
    
    has_unit_conversion = fields.Boolean(string="Has Unit Conversion ?", copy=False)
    is_right_section = fields.Boolean(string="PDP Right Section ?", copy=False)
    view_type = fields.Selection([('single','Single Value Button'),
                                  ('double','Split Value Button'),
                                  ('radio', 'Radio Button'),
                                  ('selection','Selection')], string="View Type", default="single")
    label1 = fields.Char('Label1')
    label2 = fields.Char('Label2')
    is_s3_bucket = fields.Boolean('Is S3 bucket Selection ?')

class BSProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"
    _order = "sequence"

    @api.depends('create_date','write_date','name')
    def _compute_slug(self):
        for brand in self:
            if brand.id: brand.update({'brand_slug':slug(brand)})

    image_128 = fields.Image("Image", max_width=128, max_height=128)
    is_top_brand = fields.Boolean(string="Is top brand ?", help="Set True to set this brand as a 'Top Brand'.")
    hierarchy_type = fields.Selection([('prime','Primary'),
                                       ('second','Secondary')], string="Hierarchy",copy=False)
    uom_convrsn_ids = fields.One2many('bs.attribute.uom.conversion', 'attribute_value_id', string="UOM Conversions")
    sequence = fields.Integer('Sequence', default=1, help="Used for homepage brands ordering.")
    enquiry_id = fields.Many2one('bs.enquiry')
    split_value = fields.Char('Split attribute value', copy=False)
    view_type = fields.Selection(related='attribute_id.view_type', readonly=True)
    customer_type = fields.Selection([('b2b', 'B2B'),
                                      ('b2c', 'B2C'),
                                      ('both', 'Both')], string='Customer Type', default="both")
    sku_code = fields.Char('Attribute value SKU Code', copy=False)
    brand_slug = fields.Char(string="Slug", copy=False, help="S3 bucket name same as Slug", compute = '_compute_slug', store=True)
    position = fields.Float('Position')
    category_id = fields.Many2many('product.public.category')

class BSUOMConversion(models.Model):
    _name = 'bs.attribute.uom.conversion'

    @api.depends('from_value', 'to_value', 'from_uom_id', 'to_uom_id')
    def _compute_display_name(self) :
        self.display_name = "%s %s to %s %s" % (self.from_value, self.from_uom_id.name, self.to_value, self.to_uom_id.name)

    attribute_value_id = fields.Many2one('product.attribute.value', string='Value', ondelete='cascade', copy=False)
    from_value = fields.Float(string='From', digits=(16, 3))
    to_value = fields.Float(string='To', digits=(16, 3))
    from_uom_id = fields.Many2one('uom.uom', string="From UOM")
    to_uom_id = fields.Many2one('uom.uom', string="To UOM")




class BSProdTmplAttrVals(models.Model):
    _inherit = "product.template.attribute.line"

    #Overridden
    product_tmpl_id = fields.Many2one('product.template', string="Product Template", ondelete='cascade', required=False, index=True)

    product_tmpl2_id = fields.Many2one('product.template', string="Product Template", ondelete='cascade', required=False, index=True)

    ecomm_id = fields.Many2one('product.public.category')
    is_multi_selection = fields.Boolean('Is multi Selection ?')
    
class ProductTemplateAttributeValue(models.Model):
    """Materialized relationship between attribute values
    and product template generated by the product.template.attribute.line"""

    _inherit = "product.template.attribute.value"
    
    def _without_no_variant_attributes(self):
        brand_id = self.env.ref('builderbay.brand_attribute').id
        return self.filtered(lambda ptav: ptav.attribute_id.create_variant != 'no_variant' and ptav.attribute_id.id !=brand_id)

    def _get_combination_name(self):
        """Exclude values from single value lines or from no_variant attributes."""
        return ", ".join([ptav.name for ptav in self._without_no_variant_attributes()])

    
    
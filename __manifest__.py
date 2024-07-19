{
    'name': 'builderbay ERP',
    'category': 'builderbay',
    'summary': 'Custom Implementations for builderbay Business Needs.',
    'version': '1.0',
    'description': """Feature implementations and customizations for enterprise addons to suit the needs of builderbay India Private Limited""",
    'depends': [
        'crm',
        'website',
        'website_sale', #eCommerce
        'stock', #Inventory
        'account',
        'account_intrastat', #AccountingReports
        'sale_management', #Sales,
        'website_sale_wishlist',
        'website_sale_comparison',
        'purchase',
        'l10n_in', #Indian - Accounting
        'l10n_in_hr_payroll', #Indian Payroll
        'auth_signup',
        'helpdesk',
        'sign',
        'web',

        #premium-addons
        'payment_atom',
        # 'vendor_portal_management',
        # 'vendor_product_management',

        #push notifications
        # 'ocn_client',
        # 'social_push_notifications',
    ],
    'data': [
        # security & data
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/catalog.xml',
        'data/sequence.xml',
        'data/others.xml',
        'data/ir_cron.xml',

        # qweb
        'views/qweb/signup_login.xml',
        'views/qweb/header_footer.xml',
        'views/qweb/sale.xml',
        'views/qweb/wishlist_compare.xml',
        'views/qweb/cart_checkout.xml',
        'views/qweb/portal.xml',
        'views/qweb/coming_soon.xml',

        # models
        'views/assets.xml',
        'views/res_users_view.xml',
        'views/res_partner_view.xml',
        'views/product.xml',
        'views/res_company_view.xml',
        'views/sale_order_view.xml',
        'views/generic.xml',
        'views/rfq_view.xml',
        'views/sms_log.xml',
        'views/purchase.xml',
        'views/enquiry.xml',
        'views/server_action.xml',
        'views/notifications.xml',
        'views/seo.xml',

        'reports/layout.xml',
        'reports/inv_report.xml',
        'reports/po_report.xml',
        'reports/so_report.xml',
        'reports/report_generic.xml',

        # wizards
        'wizards/generic.xml',
        'wizards/res_config_settings.xml',
    ],
    'qweb': [

        'static/src/xml/attachment.xml',

    ],
    'installable': True,
    'auto_install': False,
}

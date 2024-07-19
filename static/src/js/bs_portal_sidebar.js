odoo.define('builderbay.BSPortalSidebar', function (require) {
'use strict';

const dom = require('web.dom');
var publicWidget = require('web.public.widget');
var PortalSidebar = require('portal.PortalSidebar');
var utils = require('web.utils');

publicWidget.registry.BSPortalSidebar = PortalSidebar.extend({
    selector: '.o_portal_invoice_sidebar',
   
    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);

        var $invoiceHtml = this.$el.find('iframe#invoice_html');
        //var updateIframeSize = this._updateIframeSize.bind(this, $invoiceHtml);

        //$(window).on('resize', updateIframeSize);

        var iframeDoc = $invoiceHtml[0].contentDocument || $invoiceHtml[0].contentWindow.document;
        if (iframeDoc.readyState === 'complete') {
            //updateIframeSize();
            $('.bt_ds').prop('disabled', false);
        } 

        return def;
    },

   
});
});

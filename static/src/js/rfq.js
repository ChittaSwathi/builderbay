odoo.define('builderbay.rfq', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require("web.rpc");
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');

var QWeb = core.qweb;
var _t = core._t;


publicWidget.registry.vendor = publicWidget.Widget.extend({
    selector: '#vendor',
    events: {
    	'click #vendor_rfq': '_onLeadOrder',
		
    },
	init: function() {
        this._super.apply(this, arguments);

    },
    _onLeadOrder: function(event) {
		var uri = "/vendor/new_order";
        window.location.href = encodeURI(uri);
	},
	

  });
publicWidget.registry.wishlist = publicWidget.Widget.extend({
    selector: '#wishlist',
    events: {
    	'click .rm_wish': '_removeWishContent',
		
    },
	init: function() {
        this._super.apply(this, arguments);

    },
    _removeWishContent: function(event) {

		var order_id = $(event.target).parent().find('span.wh_order_id').text();
		ajax.jsonRpc('/remove/wish',"call", {'order_id': order_id}).then(function(result){
             location.reload(); 
        })
	},
	

  });
publicWidget.registry.price = publicWidget.Widget.extend({
    selector: '.order-list',
    events: {
    	'click #update_price': '_getOrder',
		'click .update-price':'_update_rfq_price',
		'click #rfq_accept': '_onLeadAccept',
		'click #rfq_reject': '_onLeadReject',
    },
	init: function() {
        this._super.apply(this, arguments);

    },
    _getOrder: function(event) {
		$('#detail_order').show();
		var rfq_id = $(event.target).parent().find('span.rf_id').text();
		$('#detail_order').find('tr.rf_line').remove();
		ajax.jsonRpc('/rfq/details',"call", {'rfq_id': rfq_id}).then(function(result){
               $('#detail_order tr.grand-total').before(result['rfq_dtls']);
				$('.total_uom').text(result['total_qty']);
				$('.total_vom').text();
				$('.total_base').text(result['total_bprice']);
				$('.total_rfq').text(result['rf_total']);
				$('#trans_total').val(result['rf_total']);
				$('.g_grand_total').text(result['rf_total']);
				$('.total_tax').text(result['tax_total']);
        })
	},
	_update_rfq_price: function(event) {
		$('#detail_order').find('tr.rf_line').each(function(i,row) {
		    var self = this;
		    var line_id = $(row).find('.line_id').text();
			var price = $(row).find('.v_price').val();
			var tax = $(row).find('.t_tax').val();
			var name = $(row).find('.t_description').val()
			ajax.jsonRpc('/rfq/update',"call", {'line_id': line_id,'price':price,'tax': tax, 'name': name}).then(function(result){
				
				$(row).find('.t_price').val(result['price_total']);
				$(row).find('.sub_price').val(result['price_tax']);
				$(row).find('.t_description').val(result['line_desc']);
				$('.total_uom').text(result['total_qty']);
				$('.total_vom').text();
				$('.total_base').text(result['total_bprice']);
				$('.total_rfq').text(result['rf_total']);
				$('#trans_total').val(result['rf_total']);
				$('.g_grand_total').text(result['rf_total']);
				$('.total_tax').text(result['tax_total']);
        	})
		});
	},
	_onLeadAccept: function(event) {
		var rfq_id = $(event.target).parent().parent().find('span.rf_id').text();
		ajax.jsonRpc('/rfq/accept',"call", {'rfq_id': rfq_id}).then(function(result){
           location.reload();
        })
	},
	_onLeadReject: function(event) {
		var rfq_id = $(event.target).parent().parent().find('span.rf_id').text();
		ajax.jsonRpc('/rfq/reject',"call", {'rfq_id': rfq_id}).then(function(result){
           location.reload();
        })
	},
  });
//core.action_registry.add('shipment_action', DataExport);
//return vendor;

});

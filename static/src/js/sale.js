odoo.define('builderbay.sale', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require("web.rpc");
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');
var QWeb = core.qweb;
const wUtils = require('website.utils');
var _t = core._t;
publicWidget.registry.sale = publicWidget.Widget.extend({
    selector: '#cust_crt',
    events: {
    	'click .trashIcon': '_CancelOrder',
		'click .select_order': '_CheckoutOrder',
//		'click #checkout_payment': '_redirectPayment',
		'click #checkout_payment': '_redirectStandardCart',
    },
	init: function() {
        this._super.apply(this, arguments);
    },

    _redirectStandardCart: function(e){
        let params = {};
        var orders = [];
		$('.select_order').each(function () {
		    if (this.checked){
				var order_id = $(this).parent().find('#order_id').text();
				if (order_id){
					orders.push(parseInt(order_id));
				}
			}
		});
		params.order_ids = orders
        return wUtils.sendRequest('/shop/payment', params);//http request
    },

	_redirectPayment: function(event) {

		var orders = [];
		$('.select_order').each(function () {
		    if (this.checked){
				var order_id = $(this).parent().find('#order_id').text();
				if (order_id){
					orders.push(order_id);
				}
			}
		});
		//$.post("/bs/payment", {'order_ids': orders});
		var uri = "/bs/payment?order_ids=" +orders; 
        window.location.href = encodeURI(uri);
	},
	_CheckoutOrder: function(event) {
		var self = this;
		var html = '<tr>
                      <td class="font-family-bold font-size-14 text-color-block border-left-table">
                        <p class="pad-mar-0 mar-bot-5">Order Number</p>
                        <p class="pad-mar-0 font-size-14 font-color-gray-7">Total Amount</p>
                      </td>
                      <td class="font-family-bold font-size-14 text-color-block border-right-table">
                        <p class="text-right pad-mar-0 mar-bot-5">No Order</p>
                        <p class="text-right pad-mar-0 font-size-14 font-color-gray-7">₹0.0</p>
                      </td>
                    </tr>
					<tr class="total-amount">
                      <td class="font-family-bold font-size-14 text-color-block border-left-table">
                        <p class="pad-mar-0 font-size-16 text-color-block">All Orders Total Amount</p>
                      </td>
                      <td class="font-family-bold font-size-14 text-color-block border-right-table">
                        <p class="text-right pad-mar-0 font-size-16 text-color-block">₹<span id="chk_total">0.00</span></p>
                      </td>
                    </tr>';
		var orders = [];
		$('.select_order').each(function () {
		    if (this.checked){
				var order_id = $(this).parent().find('#order_id').text();
				if (order_id){
					orders.push(order_id);
				}
			}
		});
		if(orders != ''){
			ajax.jsonRpc("/checkout_list", 'call',{
            'order_ids': orders,
	        })
	        .then(function (res) {
				$('#checkout_orders').empty();
				$('#checkout_orders').html(res['order_details']);
				$('#checkout_payment').css('background-color','#1d4da0').prop('disabled', false);
	        });
		}else{
			$('#checkout_orders').empty();
			$('#checkout_orders').html(html);
			$('#checkout_payment').css('background-color','lightgrey').prop('disabled', true);
		}
		
	},
    _CancelOrder: function(event) {
		
		var parent = $(event.target).parent().parent().find("td:first");
		var order = parent.find('#order_id').text();
		
		var self = this;
		return this._rpc({
                model: 'sale.order',
                method: 'remove_from_cart',
                args: [order],
            }).then(function(result) {
                location.reload();
        });
	},
	
  });

});

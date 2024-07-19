odoo.define('builderbay.wishlist', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require("web.rpc");
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');
var QWeb = core.qweb;
var _t = core._t;

publicWidget.registry.wishlist = publicWidget.Widget.extend({
    selector: '#wishlist',
    events: {
    	'click .add_wh_cart': '_addToCart',
		'click .rm_wish': '_removeWishlist',
    },
	init: function() {
        this._super.apply(this, arguments);

    },
    _addToCart: function(event) {
		var wish_id  = $(event.target).parent().find('.wh_order_id').text();
		rpc.query({
            model: 'customer.wishlist',
            method: 'add_to_cart',
            args: [{'wish_id':wish_id,'order_id':parseInt($(event.target).data('order-id'))}],
        }).then(function(){location.reload(true)});
		
	},
	_removeWishlist: function(event) {
		var wish_id  = $(event.target).data('order-id');
		rpc.query({
            model: 'customer.wishlist',
            method: 'remove_Wishlist',
            args: [{'order_id':parseInt(wish_id)}],
        }).then(function(){location.reload(true)});
	},

  });



});

odoo.define('builderbay.my_order', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require("web.rpc");
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');
var session = require('web.session');
var QWeb = core.qweb;
var _t = core._t;

publicWidget.registry.my_refund = publicWidget.Widget.extend({
	selector: '.bs-refund',
    events: {
    	'click .my_ord_search': '_searchOrder',
    },
	init: function() {
        this._super.apply(this, arguments);

    },
    _searchOrder: function(event) {
		var from_date = $('#order_st_date').val();
		var to_date = $('#odr_end_date').val();
		if(from_date){
		   window.location = '/my/refunds?from_date='+from_date+'&date_end=' + to_date;
        }else{
            $("#showReqDateError").show();
        }

	},
	
});
publicWidget.registry.my_order = publicWidget.Widget.extend({
    selector: '.bs-orders',
    events: {
    	'click .my_ord_search': '_searchOrder',
		'click #ledger_pdf': '_downloadPdf',
		'click #ledger_excel': '_downloadexcel',
    },
	init: function() {
        this._super.apply(this, arguments);

    },
    _searchOrder: function(event) {
		var from_date = $('#order_st_date').val();
		var to_date = $('#odr_end_date').val();
		var act_content = $('.active').find('a').text();
		if(from_date){
		    window.location = '/my/orders?from_date='+from_date+'&date_end=' + to_date+'&open_tab='+act_content;
        }else{
            $("#showReqDateError").show();
        }

	},
	_downloadPdf: function(event) {
		var from_date = $('#Start_Date').val();
		var to_date = $('#to_date').val();
		this._rpc({
                model: 'account.report',
                method: 'download_pdf',
                args: [{'date_to':to_date,'date_from':from_date}],
            }).then(function(result) {
				var self = this;
		        return new Promise(function (resolve, reject) {
		            session.get_file({
		                url: '/account_reports',
		                data: result.data,
		                
		            });
        	});
        });
	},
	_downloadexcel: function(event) {
		var from_date = $('#Start_Date').val();
		var to_date = $('#to_date').val();
		this._rpc({
                model: 'account.report',
                method: 'download_xlsx',
                args: [{'date_to':to_date,'date_from':from_date}],
            }).then(function(result) {
				var self = this;
		        return new Promise(function (resolve, reject) {
		            session.get_file({
		                url: '/account_reports',
		                data: result.data,
		                
		            });
        	});
        });
	},
  });



});

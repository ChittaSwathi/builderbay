odoo.define('builderbay.security', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require("web.rpc");
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');
var QWeb = core.qweb;
var _t = core._t;


publicWidget.registry.security = publicWidget.Widget.extend({
    selector: '.login-security',
    events: {
    	'click .user_edit': '_EditADetails',
		'click .user_save': '_saveDtails',
		'click .user_cancel': '_CancelDtails',
    },
	init: function() {
        this._super.apply(this, arguments);
		document.getElementById("psswd").readOnly = true;

    },
    _EditADetails: function(event) {
		var parent = $(event.target).parent().parent().parent();
		parent.find('p').attr('contenteditable','true');
		parent.find('p').addClass("hilight");
		document.getElementById("psswd").readOnly = false;
	},
	_saveDtails: function(event) {
		var parent = $(event.target).parent().parent().parent();
		var user_name = parent.find('span.name_user').text();
		var email = parent.find('span.email_user').text();
		var mobile = parent.find('span.user_mobile').text();
		var password = $('#psswd').val();
		this._rpc({
            model: 'res.users',
            method: 'update_user',
            args: [{'name':user_name,'email':email,'mobile':mobile,'password':password}],
        }).then(function(result) {
            swal("Success!", "Security Updated Successfully!", "success").then((ok) => {
              if (ok) {location.reload();}
            });
    	});
	},
	_CancelDtails: function(event) {
		var parent = $(event.target).parent().parent().parent();
		parent.find('p').attr('contenteditable','false');
		parent.find('p').removeClass("hilight");
		document.getElementById("psswd").readOnly = true;
	},

  });



});

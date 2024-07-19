odoo.define('builderbay.address', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require("web.rpc");
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');
var QWeb = core.qweb;
var _t = core._t;

    publicWidget.registry.modaladdress = publicWidget.Widget.extend({
        selector: '#PortalModifyAddress',
        events: {
            'click #SubmitModalAddress': '_SubmitAddress',
        },
        init: function() {
            this._super.apply(this, arguments);
        },
        _SubmitAddress: function(event) {
            var AddID = $(event.target).attr('address-id')
            var AddType = $(event.target).attr('type')
            return false
        },
      });

    publicWidget.registry.address = publicWidget.Widget.extend({
        selector: '#cus_address',
        events: {
            'click #edit_addr': '_editAdd',
            'click #bill_rmv': '_removeAddr',
            'click #setDefault': '_setDefault',
            'click #addShippingAddress': '_addShippingAdd',
            'click #addBillingAddress': '_addBillingAdd'
        },
        init: function() {
            this._super.apply(this, arguments);
        },
        _EditAddr: function(event) {
            if ($(event.target).text().trim() == "Edit") {
                var parent = $(event.target).parent().parent().parent().parent().parent().parent();
                parent.find('span').attr('contenteditable','true');
                parent.find('span').addClass("hilight");
                $(event.target).text("Save");
            } else {
                var parent = $(event.target).parent().parent().parent();
                var addr_id = parent.find('span').text();
                var sup_parent = $(event.target).parent().parent().parent().parent().parent().parent();
                var bill_name = sup_parent.find('span.billname').text().trim();
                var street1 = sup_parent.find('span.street1').text().trim();
                var street2 = sup_parent.find('span.street2').text().trim();
                var city = sup_parent.find('span.city').text().trim();
                var pin = sup_parent.find('span.pin').text().trim();
                var mobile = sup_parent.find('span.mobile').text().trim();
                this._rpc({
                    model: 'res.partner',
                    method: 'update_address',
                    args: [{'addr_id':addr_id,'name':bill_name,'street':street1,'street2':street2,'city':city,'zip':pin,'mobile':mobile}],
                }).then(function(result) {
                    swal("Success!", "Address Updated Successfully!", "success");
                });
                $(event.target).text("Edit");
                sup_parent.find('span').attr('contenteditable','false');
                sup_parent.find('span').removeClass("hilight");
            }

        },
        _removeAddr: function(event) {
            var parent = $(event.target).parent().parent().parent();
            var addr_id = parent.find('span').text();
            this._rpc({
                    model: 'res.partner',
                    method: 'removeAddr',
                    args: [{'addr_id':addr_id}],
                }).then(function(result) {
                    swal({
                      title: "Are you sure want to remove it?",
                      text: "Once removed, you will not be able to recover this address!",
                      icon: "warning",
                      buttons: true,
                      dangerMode: true,
                    })
                    .then((willDelete) => {
                      if (willDelete) {
                            if (result == true) {
                                swal("Success!", "Successfully removed!", "success").then(function(){
                                    location.reload();
                                });
                            }
                            else if (result == false){
                                swal("Success!", "Something went wrong. Please try again.", "success");
                            }
                            else {
                                swal("Information!", "Cannot remove this address as it is linked with a Sale Order.", "warning");
                            }
                      } else {
                        swal("Address is not removed!");
                      }
                    });
            });
        },
        _setDefault: function(event) {
            var parent = $(event.target).parent();
            var addr_id = $(event.target).attr('address-id');
            this._rpc({
                    model: 'res.partner',
                    method: 'setDefaultAddr',
                    args: [{'addr_id':addr_id}],
                }).then(function(result) {
                    location.reload();
            });
        },
        _addBillingAdd: function(event) {
            ajax.jsonRpc('/modal/address',"call", {'address_id':false,'type':'invoice',
             }).then(function(ModalPopup){
                $(ModalPopup).appendTo('body').modal();
                setTimeout(function(){
                    $( ".PortalModifyAddress" ).each(function( index,element ) {
                        if($(this).is(":visible")){
                        }else{
                            $(this).remove();
                        }
                    });
                }, 1000);
            })
        },
        _addShippingAdd: function(event) {
            ajax.jsonRpc('/modal/address',"call", {'address_id':false,'type':'delivery',
             }).then(function(ModalPopup){
                $(ModalPopup).appendTo('body').modal();
                setTimeout(function(){
                    $( ".PortalModifyAddress" ).each(function( index,element ) {
                        if($(this).is(":visible")){
                        }else{
                            $(this).remove();
                        }
                    });
                }, 1000);
            });
        },
        _editAdd: function(event) {
            var AddID = $(event.target).attr('address-id')
            var AddType = $(event.target).attr('type')
             ajax.jsonRpc('/modal/address',"call", {'address_id':AddID,'type':AddType,
             }).then(function(ModalPopup){
                $(ModalPopup).appendTo('body').modal();
                setTimeout(function(){
                    $( ".PortalModifyAddress" ).each(function( index,element ) {
                        if($(this).is(":visible")){
                        }else{
                            $(this).remove();
                        }
                    });
                }, 1000);
            });
        },
      });



});

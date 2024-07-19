odoo.define('builderbay.bs_portal', function(require) {

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var rpc = require("web.rpc");
    var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
    var AllCharsRegex = /^[ A-Za-z]+$/;
    var GSTRegex = /^([0][1-9]|[1-2][0-9]|[3][0-7])([a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}[1-9a-zA-Z]{1}[zZ]{1}[0-9a-zA-Z]{1})+$/;
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var publicWidget = require('web.public.widget');
    var QWeb = core.qweb;
    var _t = core._t;
    var Widget = require('web.Widget');
    const wUtils = require('website.utils');

    function encodeImageFileAsURL(cb) {
        return function(){
            var file = this.files[0];
            var reader  = new FileReader();
            reader.onloadend = function () { cb(reader.result); }
            reader.readAsDataURL(file);
        }
    }
    /* Generic function that returns base64 string */

    publicWidget.registry.clickUpload = publicWidget.Widget.extend({
        selector: '.click-upload',
        events: {
            // 'change #enquiry_attachment':  '_onChangeEnqAttach',
            // 'change #delivery_attachment':  '_onChangeDelAttach',
            'change #contact_person': '_onchangeContPersn',
            'change #phone': '_onchangePhn',
            'change #gstin': '_onchangeGSTIN',
            'change #trade_name': '_onchangeTradeName',
            'change #address': '_onchangeAddress',
            'click #submit_click_upload': '_onSubmitForm',
        },
        init: function() {
            this._super.apply(this, arguments);
        },
        readURL: function(input, EleID, Eleb64) {
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    $('#'+EleID).css('background-image', 'url('+e.target.result +')');
                    $('#'+EleID).hide();
                    $('#'+EleID).fadeIn(650);
                    $(Eleb64+'_base64').val(e.target.result.replace(/^data:.+;base64,/, '')).attr('src',e.target.result);
                    $(Eleb64+'_label').html(input.files[0]['name']);
                }
                reader.readAsDataURL(input.files[0]);
            }
        },
        _onChangeEnqAttach: function(base64Img){
            this.readURL(base64Img.target, 'enq-attach-preview','#enquiry_attachment');
        },
        _onChangeDelAttach: function(base64Img){
            this.readURL(base64Img.target, 'del-attach-preview', '#delivery_attachment');
        },
        _onchangeContPersn: function(e){
            var Name = e.target.value
            if ((Name.length == 0) || (!AllCharsRegex.test(Name))) {
                $("#"+ e.target.id +"_error").html("Please enter a valid name.").show();
            } else {
                $("#"+ e.target.id +"_error").html("").hide();
            }
        },
        _onchangePhn: function(e){
            var Phone = e.target.value
            if ((Phone.length < 10) || (!MobileRegex.test(Phone))) {
                $("#"+ e.target.id +"_error").html("Please enter a valid phone number.").show();
            } else {
                $("#"+ e.target.id +"_error").html("").hide();
            }
        },
        _onchangeGSTIN: function(e){
            var GST = e.target.value
            if ((GST.length != 15) || (!GSTRegex.test(GST))) {
                if (($('#customer-type').val() == 'b2c' && GST.length == 0)){
                    $("#"+ e.target.id +"_error").html("").hide();
                }
                else{
                    $("#"+ e.target.id +"_error").html("Please enter a valid GSTIN.").show();
                }
            } else {
                $("#"+ e.target.id +"_error").html("").hide();
            }
        },
        _onchangeTradeName: function(e){
            var TName = e.target.value
            if (TName.length == 0) {
                if (($('#customer-type').val() == 'b2c' && TName.length == 0)){
                    $("#"+ e.target.id +"_error").html("").hide();
                }
                else{
                    $("#"+ e.target.id +"_error").html("Please enter a valid trade name.").show();
                }
            } else {
                $("#"+ e.target.id +"_error").html("").hide();
            }
        },
        _onchangeAddress:function(e){
            var AName = e.target.value
            if (AName.length == 0) {
                $("#"+ e.target.id +"_error").html("Please enter your registered address.").show();
            } else {
                $("#"+ e.target.id +"_error").html("").hide();
            }
        },
        _onSubmitForm: function(e){
            var valid = true;
            FinalVals = {}
            $('#click-upload-form input:visible').each(function(){

                inputName = $(this).attr("name");
                if(inputName == 'enquiry_attachment'){
                    var isEmptyenqObj = jQuery.isEmptyObject(uploadEnquiryObj);
                    if(isEmptyenqObj === true){
                        valid = false;
                        $("#"+ $(this).attr("id") +"_error").html("Please upload enquiry attachment file or image.").show();
                    }else{
                        $("#"+ $(this).attr("id") +"_error").html("").hide();
                        FinalVals['documents'] = uploadEnquiryObj
                    }
                }
                if(inputName == 'delivery_attachment'){
                    var isEmptyenqDelObj = jQuery.isEmptyObject(uploadDeliveryObj);
                    if(isEmptyenqDelObj === true){
                        valid = false;
                        $("#"+ $(this).attr("id") +"_error").html("Please upload delivery attachment file or image.").show();
                    }else{
                        $("#"+ $(this).attr("id") +"_error").html("").hide();
                        FinalVals['delivery'] = uploadDeliveryObj
                    }
                }
                if(inputName == 'contact_person'){
                    var Name = $(this).val();
                    if ((Name.length == 0) || (!AllCharsRegex.test(Name))) {
                        valid = false;
                        $("#"+ $(this).attr("id") +"_error").html("Please enter a valid name.").show();
                    } else {
                        $("#"+ $(this).attr("id") +"_error").html("").hide();
                        FinalVals['name'] = Name
                    }
                }
                if(inputName == 'phone'){
                    var Phone = $(this).val();
                    if ((Phone.length < 10) || (!MobileRegex.test(Phone))) {
                        valid = false;
                        $("#"+ $(this).attr("id") +"_error").html("Please enter a valid phone number.").show();
                    } else {
                        $("#"+ $(this).attr("id") +"_error").html("").hide();
                        FinalVals['phone'] = Phone
                    }
                }
                if ($('#customer-type').val() == 'b2b' || $('#gstin').val()){
                    if(inputName == 'gstin'){
                        var GST = $(this).val();
                        if ((GST.length != 15) || (!GSTRegex.test(GST))) {
                            valid = false;
                            $("#"+ $(this).attr("id") +"_error").html("Please enter a valid GSTIN.").show();
                        } else {
                            $("#"+ $(this).attr("id") +"_error").html("").hide();
                            FinalVals['gstin'] = GST
                        }
                    }
                }
                if ($('#customer-type').val() == 'b2b' ||  $('#trade_name').val()){
                    if(inputName == 'trade_name'){
                        var TName = $(this).val();
                        if (TName.length == 0) {
                            valid = false;
                            $("#"+ $(this).attr("id") +"_error").html("Please enter a valid trade name.").show();
                        } else {
                            $("#"+ $(this).attr("id") +"_error").html("").hide();
                            FinalVals['trade_name'] = TName
                        }
                    }
                }
            })
            $('#click-upload-form textarea:visible').each(function(){ //text area Fields
                Address = $(this).val();
                if(Address == ""){
                    valid = false;
                    $("#"+ $(this).attr("id") +"_error").html('Please enter your registered address.').show();
                }else {
                    $("#"+ $(this).attr("id") +"_error").html('').hide();
                    FinalVals['address'] = Address
                }
            })
            if(valid){
                FinalVals['type'] = 'ClickUpload'
                ajax.jsonRpc("/create/enquiry", 'call',FinalVals)
                .then(function (res) {
                    if (res){
                        swal("Success!", "Your Enquiry has been placed successfully.", "success").then((ok) => {
                          if (ok) {window.location.href = "/my/enquiries?tab=click";}
                        });
                    }
                    else
                    {
                        swal("OOPS!", `Something went wrong. Please retry.`, "error");
                    }
                });

            }
//            if ($('.click-upload #enquiry_attachment_base64').val() &&
//                $('.click-upload #delivery_attachment_base64').val() &&
//                $('.click-upload #contact_person').val() &&
//                $('.click-upload #phone').val() &&
//                $('.click-upload #gstin').val() &&
//                $('.click-upload #trade_name').val() &&
//                $('.click-upload #address').val()){
//                    $('#submit-error').html('').hide();
//                    $('#click-upload-form').submit();
//            }
//            else{
//
//                $('#submit-error').html('Please recheck values.').show();
//                return false
//            }

        },
    });

    // upload document for price enq
    var uploadEnquiryObj = {};
    $(function () {
        var dvPreview = $("#priceEnqPreview");
        dvPreview.html("");
        $("#enquiry_attachment").change(function () {
            if (typeof (FileReader) != "undefined") {
                var regex = /^([a-zA-Z0-9\s_\\.\-:])+(.jpg|.jpeg|.gif|.png|.bmp)$/;
                $($(this)[0].files).each(function (index) {
                    var file = $(this);
                    var reader = new FileReader();
                    var ext = file[0].name.split('.').pop();
                    var fileSize = parseFloat(file[0].size / (1024 * 1024)).toFixed(2);
                    if(fileSize > 4) {
                        swal("OOPS!", `${file[0].name} too Big, Please select file/Image size less than 4 MB.`, "error");
                    }else{
                        reader.onload = function (e) {
                        if(regex.test(file[0].name.toLowerCase())){
                            var divCreate = $("<div class='imgRepeatDiv'><img src='https://cdn3.iconfinder.com/data/icons/faticons/32/remove-01-512.png' class='removeIcon'/>");
                            var img = $("<img />");
                            img.attr("style", "height:60px;width: 60px;float:left;margin-right:5px;border:1px solid #ddd;margin-bottom: 5px;");
                            img.attr("src", e.target.result);
                            img.attr("class", [file[0].name]+'penq', 'dynamicContent')
                            img.attr("id", [file[0].name]+'penq')
                            divCreate.append(img)
                            dvPreview.append(divCreate);
                            uploadEnquiryObj[[file[0].name]] = e.target.result;
                            $("#enquiry_attachment_error").html("").hide();
                        }else if(ext == "pdf" || ext == "docx" || ext == "doc" || ext == "txt" || ext == "csv" || ext == "xls" || ext == "xlsx"){
                            var divCreate = $("<div class='imgRepeatDiv'><img src='https://cdn3.iconfinder.com/data/icons/faticons/32/remove-01-512.png' class='removeIcon'/>");
                            var pTag = $("<p></p>");
                            pTag.attr("style", "float:left;margin-right:5px;border: 1px solid #ddd;padding: 5px;height: 60px;margin-bottom: 5px;line-height: 40px;font-family:Lato-Regular;");
                            pTag.attr("class", [file[0].name]+'penq')
                            pTag.attr("id", [file[0].name]+'penq')
                            pTag.text(file[0].name);
                            divCreate.append(pTag)
                            dvPreview.append(divCreate);
                            uploadEnquiryObj[[file[0].name]] = e.target.result;
                            $("#enquiry_attachment_error").html("").hide();
                        }else{
                            swal("OOPS!", `Uploaded wrong ${file[0].name} file.`, "error");
                        }
                    }
                        reader.readAsDataURL(file[0]);
                    }
                });
            } else {
                swal("OOPS!", "This browser does not support HTML5 FileReader.", "error");
            }
            setTimeout(function(){
                removeDuplicates();
            },100)
        });
        function removeDuplicates(){
            $('#priceEnqPreview img').each(function () {
                $('[id="' + this.id + '"]:gt(0)').remove();
            });
            $('#priceEnqPreview p').each(function () {
                $('[id="' + this.id + '"]:gt(0)').remove();
            });
            $("#priceEnqPreview .imgRepeatDiv").map(function() {
                if(this.children.length === 1){
                    $(this).remove();
                }
            })
        }
    });
    $(document).on('click', '.removeIcon', function(){
        var ID = $(this).next().attr("id");
        var substringKey = ID.slice(0, -4);
        $(this).next().remove();
        $(this).remove();
        delete uploadEnquiryObj[substringKey];
    });
    // upload document for price enq

    // upload document for Delivery Address
    var uploadDeliveryObj = {};
    $(function () {
        var dvPreview = $("#deliveryAddressPreview");
        dvPreview.html("");
        $("#delivery_attachment").change(function () {
            if (typeof (FileReader) != "undefined") {
                var regex = /^([a-zA-Z0-9\s_\\.\-:])+(.jpg|.jpeg|.gif|.png|.bmp)$/;
                $($(this)[0].files).each(function (index) {
                    var file = $(this);
                    var reader = new FileReader();
                    var ext = file[0].name.split('.').pop();
                    var fileSize = parseFloat(file[0].size / (1024 * 1024)).toFixed(2);
                    if(fileSize > 4) {
                        swal("OOPS!", `${file[0].name} too Big, Please select file/Image size less than 4 MB.`, "error");
                    }else{
                        reader.onload = function (e) {
                        if(regex.test(file[0].name.toLowerCase())){
                            var divCreate = $("<div class='imgRepeatDiv'><img src='https://cdn3.iconfinder.com/data/icons/faticons/32/remove-01-512.png' class='removeIconDel'/>");
                            var img = $("<img />");
                            img.attr("style", "height:60px;width: 60px;float:left;margin-right:5px;border:1px solid #ddd;margin-bottom: 5px;");
                            img.attr("src", e.target.result);
                            img.attr("class", [file[0].name]+'del')
                            img.attr("id", [file[0].name]+'del')
                            divCreate.append(img)
                            dvPreview.append(divCreate);
                            uploadDeliveryObj[[file[0].name]] = e.target.result;
                        }else if(ext == "pdf" || ext == "docx" || ext == "doc" || ext == "txt" || ext == "csv" || ext == "xls" || ext == "xlsx"){
                            var divCreate = $("<div class='imgRepeatDiv'><img src='https://cdn3.iconfinder.com/data/icons/faticons/32/remove-01-512.png' class='removeIconDel'/>");
                            var pTag = $("<p></p>");
                            pTag.attr("style", "float:left;margin-right:5px;border: 1px solid #ddd;padding: 5px;height: 60px;margin-bottom: 5px;line-height: 40px;font-family:Lato-Regular;");
                            pTag.attr("class", [file[0].name]+'del')
                            pTag.attr("id", [file[0].name]+'del')
                            pTag.text(file[0].name);
                            divCreate.append(pTag)
                            dvPreview.append(divCreate);
                            uploadDeliveryObj[[file[0].name]] = e.target.result;
                        }else{
                            swal("OOPS!", `Uploaded wrong ${file[0].name} file.`, "error");
                        }
                    }
                        reader.readAsDataURL(file[0]);
                    }

                });
            } else {
                swal("OOPS!", "This browser does not support HTML5 FileReader.", "error");
            }
            setTimeout(function(){
                removeDuplicatesDel();
            },100)
        });
        function removeDuplicatesDel(){
            $('#deliveryAddressPreview img').each(function () {
                $('[id="' + this.id + '"]:gt(0)').remove();
            });
            $('#deliveryAddressPreview p').each(function () {
                $('[id="' + this.id + '"]:gt(0)').remove();
            });
            $("#deliveryAddressPreview .imgRepeatDiv").map(function() {
                if(this.children.length === 1){
                    $(this).remove();
                }
            })
        }
    });

    // create support ticket form start
    const subject = document.getElementById('subject');
    if(subject){
        subject.addEventListener('change', onChangesubject);
    }
    function onChangesubject(e) {
      if(e.target.value == ''){
        $("#error_subject").html("Please enter valid subject.").show();
      }else{
        $("#error_subject").html("").hide();
      }
    }
    const description = document.getElementById('description');
    if(description){
        description.addEventListener('change', onChangedescription);
    }
    function onChangedescription(e) {
      if(e.target.value == ''){
        $("#error_ticket_description").html("Please enter description.").show();
      }else{
        $("#error_ticket_description").html("").hide();
      }
    }
    $('#ticket_type_id').on('change', function(e) {
        if (e.target.value == 0){
            $("#error_ticket_type").html("Please select ticket type.").show();
        }else{
            $("#error_ticket_type").html("").hide();
        }
    });

    $(function() {
        $('.line-text-clamp').each(function(i) {
            var element = $(this).clone().css({display: 'inline', width: 'auto', visibility: 'hidden'}).appendTo('body');
            if( element.width() > $(this).width() ) {
                $(this).next().css({"display": "show"});
            }else{
                $(this).next().css({"display": "none"});
            }
            element.remove();
        });
    });
    // edit address modal start
//    $('#addShippingAddress').click(function(){
//        ajax.jsonRpc('/edit/address',"call", {'address_id':false,'type':'shipping',
//         }).then(function(ModalPopup){
//            $(ModalPopup).appendTo('body').modal();
//        })
//    });
//    $('#addBillingAddress').click(function(){
//        ajax.jsonRpc('/edit/address',"call", {'address_id':false,'type':'billing',
//         }).then(function(ModalPopup){
//            $(ModalPopup).appendTo('body').modal();
//        })
//    });
//    $("#edit_addr").click(function(){
//         ajax.jsonRpc('/edit/address',"call", {'address_id':$(this).attr('address-id'),'type':$(this).attr('type'),
//         }).then(function(ModalPopup){
//            $(ModalPopup).appendTo('body').modal();
//        })
//    });
    // edit address modal ends
    $("#supportTicket").submit(function(event) {
        let name = document.forms["supportTicketForm"]["name"].value;
        let description = document.forms["supportTicketForm"]["description"].value;

        var validsupportTicketForm = true;
        if(name == ''){
            $("#error_subject").html("Please enter valid subject.").show();
            validsupportTicketForm = false;
        }else{
            $("#error_subject").html("").hide();
        }

        if(description == ''){
            $("#error_ticket_description").html("Please enter description.").show();
            validsupportTicketForm = false;
        }else{
            $("#error_ticket_description").html("").hide();
        }

        if ($("#ticket_type_id").val() == 0){
            $("#error_ticket_type").html("Please select ticket type.").show();
            validAddressForm = false;
        }else{
            $("#error_ticket_type").html("").hide();
        }

        if(!validsupportTicketForm){
           return false;
        }else{
            swal("Success!", "Ticket successfully created!", "success");
        }
    });
    // create support ticket form ends

    // Add address modal validations start
    $(document).on("click", ".submitAddressForm", function(event){
        let name = document.forms["validateAddressForm"]["name"].value;
        let Mobile = document.forms["validateAddressForm"]["mobile"].value;
        let address = document.forms["validateAddressForm"]["street"].value;
        let site_name = document.forms["validateAddressForm"]["site_name"].value;
        let landmark = document.forms["validateAddressForm"]["landmark"].value;
        let city = document.forms["validateAddressForm"]["city"].value;
        let zip = document.forms["validateAddressForm"]["zip"].value;
        var validAddressForm = true;
        var FinalVals = {'name':name, 'mobile':Mobile, 'street':address,'street2':$('#inputAddress2').val(),
                        'site_name':site_name, 'landmark':landmark,'city':city, 'zip':zip,
                        'type':$('#validateAddressForm').attr('address-type')}
        if(name == ''){
            $("#error_inputEmail4").html("Please enter valid contact name.").show();
            validAddressForm = false;
        }else{
            $("#error_inputEmail4").html("").hide();
        }
        if ($("#inputState").val() == 0){
            $("#state_error").html("Please select state.").show();
            validAddressForm = false;
        }else{
            FinalVals['state_id'] = parseInt($("#inputState").val());
            $("#state_error").html("").hide();
        }

        if ($("#district_id").val() == 0){
            $("#district_error").html("Please select district.").show();
            validAddressForm = false;
        }else{
            FinalVals['district_id'] = parseInt($("#district_id").val());
            $("#district_error").html("").hide();
        }

        var AllNumericRegex= /^[0-9]+$/;
        if(zip == ""){
            $("#zip_error").html('Please enter your pincode.').show();
            validAddressForm = false;
        }else if((zip.length < 6) || (!AllNumericRegex.test(zip))){
            $("#zip_error").html("Please enter a valid pincode.").show();
            validAddressForm = false;
        }else {
            $("#zip_error").html('').hide();
        }

        if(address == ''){
            $("#address_error").html("Please enter valid address.").show();
            validAddressForm = false;
        }else{
            $("#address_error").html("").hide();
        }

        if(site_name == ''){
            $("#site_name_error").html("Please enter valid site name.").show();
            validAddressForm = false;
        }else{
            $("#site_name_error").html("").hide();
        }

        if(landmark == ''){
            $("#landmark_error").html("Please enter valid land mark.").show();
            validAddressForm = false;
        }else{
            $("#landmark_error").html("").hide();
        }

        if(city == ''){
            $("#city_error").html("Please enter valid city.").show();
            validAddressForm = false;
        }else{
            $("#city_error").html("").hide();
        }

        var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if(Mobile == ""){
            $('#mobile_error').html('Please enter your mobile number.').show();
            validAddressForm = false;
        }else if(!MobileRegex.test(Mobile) || (Mobile.length < 10)){
            $("#mobile_error").html("Please enter valid mobile number.").show();
            validAddressForm = false;
        }else{
            $("#mobile_error").html("").hide();
        }

        if(!validAddressForm){
           return false;
        }else{
            if ($(this).attr('address-id') != false){
                FinalVals['address-id'] = $('#validateAddressForm').attr('address-id')
                ajax.jsonRpc('/edit/address',"call", FinalVals).then(function(result){
                    if (result != false){
                        swal("Success!", "Address modified successfully!", "success").then((ok) => {
                          if (ok) {window.location ='/my/address/?tab='+result;}
                        });
                    }
                    else{swal("OOPS!", `Something went wrong.`, "error");}
                })
            }
            else{
                 ajax.jsonRpc('/add/address',"call", FinalVals).then(function(result){
                    if (result != false){
                        swal("Success!", "Address successfully created!", "success").then((ok) => {
                          if (ok) {window.location ='/my/address/?tab='+result;}
                        });
                    }
                    else{swal("OOPS!", `Something went wrong.`, "error");}
                })
            }
        }
    });

    $(document).on('keyup', '#inputEmail4', function(e) {
      if(e.target.value == ''){
        $("#error_inputEmail4").html("Please enter valid contact name.").show();
      }else{
        $("#error_inputEmail4").html("").hide();
      }
    });

    $(document).on('keyup', '#inputPassword4', function(e) {
      var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if(e.target.value == ""){
            $('#mobile_error').html('Please enter your mobile number.').show();
        }else if(!MobileRegex.test(e.target.value) || (e.target.value.length < 10)){
            $("#mobile_error").html("Please enter valid mobile number.").show();
        }else{
            $("#mobile_error").html("").hide();
        }
    });

    $(document).on('keyup', '#inputAddress', function(e) {
      if(e.target.value == ''){
            $("#address_error").html("Please enter valid address.").show();
        }else{
            $("#address_error").html("").hide();
        }
    });


    $(document).on('keyup', '#inputSitename', function(e) {
      if(e.target.value == ''){
            $("#site_name_error").html("Please enter valid site name.").show();
        }else{
            $("#site_name_error").html("").hide();
        }
    });

    $(document).on('keyup', '#inputlandmark', function(e) {
      if(e.target.value == ''){
            $("#landmark_error").html("Please enter valid land mark.").show();
        }else{
            $("#landmark_error").html("").hide();
        }
    });

    $(document).on('keyup', '#inputCity', function(e) {
      if(e.target.value == ''){
            $("#city_error").html("Please enter valid city.").show();
        }else{
            $("#city_error").html("").hide();
        }
    });

    $(document).on('change', '#inputState', function(e) {
      if (e.target.value == 0){
            $("#state_error").html("Please select state.").show();
        }else{
            $("#state_error").html("").hide();
        }
    });

    $(document).on('change', '#district_id', function(e) {
      if (e.target.value == 0){
            $("#district_error").html("Please select state.").show();
        }else{
            $("#district_error").html("").hide();
        }
    });

    $(document).on('keyup', '#inputZip', function(e) {
      var AllNumericRegex= /^[0-9]+$/;
        if(e.target.value == ""){
            $("#zip_error").html('Please enter your pincode.').show();
        }else if((e.target.value.length < 6) || (!AllNumericRegex.test(e.target.value))){
            $("#zip_error").html("Please enter a valid pincode.").show();
        }else {
            $("#zip_error").html('').hide();
        }
    });
    $("#delAddressModel").click(function () {
        $("#inlineRadio2").prop("checked", true);
    });
    $("#bilAddressModel").click(function () {
        $("#inlineRadio1").prop("checked", true);
    });
    // Add address modal validations ends

    // Login & Security : change password confirm password validations start
    $(".password-eye-icon").click(function(){
        var elmId = $(this).attr("id").substring(3);
        var img = document.getElementById($(this).attr("id")).src;
        if (img.indexOf('eye-slash.png')!=-1) {
            document.getElementById($(this).attr("id")).src  = '/builderbay/static/src/images/eye.png';
        }else{
           document.getElementById($(this).attr("id")).src = '/builderbay/static/src/images/eye-slash.png';
        }
        var showPasswordInput = document.getElementById(elmId);
        if (showPasswordInput.type === "password") {
            showPasswordInput.type = "text";
        } else {
            showPasswordInput.type = "password";
        }
    });
    $("#changePassword").click(function(){
        $("#showChangePassword").show();
        $(this).hide();
    });
    $("#cancelChangePassword").click(function(){
        $("#showChangePassword").hide();
        $("#changePassword").show();
    });

    var validatePasswordCheck = true;
    $('.card-login-sequrity .submit-password-btn').click(function(e){
        validatePasswordCheck = true;
        PasswordCurrentCheckLength();
        PasswordNewCheckLength();
        checkPasswordMatch();
        if(validatePasswordCheck){
                    ajax.jsonRpc('/change/password',"call", {'CurrentPassword': $('.card-login-sequrity #currentPassword').val(),
                                                    'NewPassword': $('.card-login-sequrity #newPassword').val(),
                                                    'ConfirmPassword': $('.card-login-sequrity #confirmPassword').val()
            }).then(function(result){
               if (result){
                swal("Success!", "Successfully changed the password!", "success").then((ok) => {
                  if (ok) {location.reload()}
                });
               }
               else{
                swal("Error!", "Incorrect current password!", "error");
               }
            })
        }
    })

    $(".card-login-sequrity #currentPassword").keyup(PasswordCurrentCheckLength);
    function PasswordCurrentCheckLength(){
        var passwordLength = $(".card-login-sequrity #currentPassword").val();
        if(passwordLength == ""){
            $('#error_currentPassword').html('Please enter current password.').show();
            validatePasswordCheck = false;
        }else {
            $('#error_currentPassword').html('').hide();
        }
    }
    $(".card-login-sequrity #newPassword").keyup(PasswordNewCheckLength);
    function PasswordNewCheckLength(){
        var passwordLength = $(".card-login-sequrity #newPassword").val();
        if(passwordLength == ""){
            $('#error_newPassword').html('Please enter new password.').show();
            validatePasswordCheck = false;
        }else if(passwordLength.length < 6){
            $('#error_newPassword').html('You have to enter at least 6 characters.').show();
            validatePasswordCheck = false;
        }else {
            $('#error_newPassword').html('').hide();
        }
    }
    $(".card-login-sequrity #confirmPassword").keyup(checkPasswordMatch);
    function checkPasswordMatch() {
        $(".signupIndCustomer #error_CheckPasswordMatch").html("");
        PasswordNewCheckLength();
        var confirm_password = $('.card-login-sequrity #confirmPassword').val();
        var password = $(".card-login-sequrity #newPassword").val();
        if(confirm_password == ""){
            $("#error_CheckPasswordMatch").html("Please enter confirm password.");
            validatePasswordCheck = false;
        }else if (password != confirm_password) {
            $("#error_CheckPasswordMatch").html("Passwords does not match!");
            validatePasswordCheck = false;
        }
        else {
            $("#error_CheckPasswordMatch").html("");
        }
    }
    // change password confirm password validations ends

    $(document).on('click', '.removeIconDel', function(){
        var ID = $(this).next().attr("id");
        var substringKey = ID.slice(0, -3);
        $(this).next().remove();
        $(this).remove();
        delete uploadDeliveryObj[substringKey];
    });

	/* open order cancel*/
	$('#open_od_cancel').click(function(){
	    swal({
          title: "Are you sure?",
          text: "Order will be moved to cancelled state !",
          icon: "warning",
          buttons: ['Close!', 'Yes Cancel!'],
          dangerMode: true,
        })
        .then((willDelete) => {
          if (willDelete) {
            rpc.query({
            model: 'sale.order',
            method: 'cancel_open_order',
            args: [{'order_id':parseInt($(this).attr('order_id'))}],
        }).then(function(){
            swal("Your order has been canceled!", {
              icon: "success",
            }).then((ok) => {
              if (ok) {window.location.href = "/my/orders?tab=cancel";}
            });
        });
          } else {
            swal("Your order hasn't been canceled!");
          }
        });
    })
	/* end */
    /* Add GSTIN starts */
    $('.manage-gst #delete_gst').click(function(){
        rpc.query({
            model: 'bs.gst',
            method: 'write',
            args: [parseInt($(this).attr('gst-id')), {
                'partner_id':false,
            }],
        }).then(function(){location.reload(true)});
    })
    $('.manage-gst #manage_gst').click(function(){
        ajax.jsonRpc('/gst/edit',"call", {'gst_id':$(this).attr('gst-id')}).then(function(ManageGST){
            $(ManageGST[0]).appendTo('body').modal();
        })
    })

    $('#bs_addgst_modal #gstin').change(function(){
        if (!$(this).val()){$('#bs_addgst_modal #gstin_error').html('Please enter GSTIN.').show()}
        else if (!GSTRegex.test($(this).val())){$('#bs_addgst_modal #gstin_error').html('Please enter a valid GSTIN.').show()}
        else{$('#bs_addgst_modal #gstin_error').hide()}
    })
    $('#bs_addgst_modal #legal_name').change(function(){
        if (!$(this).val()){$('#bs_addgst_modal #legal_name_error').html('Please enter legal name.').show()}
        else{$('#bs_addgst_modal #legal_name_error').hide()}
    })
    $('#bs_addgst_modal #shop_name').change(function(){
        if (!$(this).val()){$('#bs_addgst_modal #shop_name_error').html('Please enter shop name.').show()}
        else{$('#bs_addgst_modal #shop_name_error').hide()}
    })
    $('#bs_addgst_modal #reg_address').change(function(){
        if (!$(this).val()){$('#bs_addgst_modal #reg_address_error').html('Please enter registered address.').show()}
        else{$('#bs_addgst_modal #reg_address_error').hide()}
    })
    $('#bs_addgst_modal #gst_city').change(function(){
        if (!$(this).val()){$('#bs_addgst_modal #gst_city_error').html('Please enter city.').show()}
        else{$('#bs_addgst_modal #gst_city_error').hide()}
    })
    $('#bs_addgst_modal #gst_zip').change(function(){
        if (!$(this).val()){$('#bs_addgst_modal #gst_zip_error').html('Please enter zipcode.').show()}
        else if (!$.isNumeric($(this).val())){$('#bs_addgst_modal #gst_zip_error').html('Please enter a valid zipcode.').show()}
        else{$('#bs_addgst_modal #gst_zip_error').hide()}
    })
    $('#bs_addgst_modal #mobile').change(function(){
        if (!$(this).val()){$('#bs_addgst_modal #mobile_error').html('Please enter mobile no.').show()}
        else if (!MobileRegex.test($(this).val())){$('#bs_addgst_modal #mobile_error').html('Please enter a valid mobile no.').show()}
        else{$('#bs_addgst_modal #mobile_error').hide()}
    })
     $('#bs_addgst_modal #gst_state_id').change(function(){
        if (!$('#bs_addgst_modal #gst_state_id option:selected').attr('id')){$('#bs_addgst_modal #gst_state_id_error').html('Please select state.').show()}
        else{$('#bs_addgst_modal #gst_state_id_error').hide()}
    })

    $('#bs_addgst_modal #add_gstin').click(function(){
        var valid=true
        var GSTVals = {}

        if (!$('#gstin').val()){valid=false;$('#gstin_error').html('Required').show()}
        else if (GSTRegex.test($(this).val())){valid=false;$('#bs_addgst_modal #gstin_error').html('Please enter a valid GSTIN.').show()}
        else{$('#gstin_error').hide();GSTVals['gstin'] = $('#gstin').val()}

        if (!$('#legal_name').val()){valid=false;$('#legal_name_error').html('Required').show()}
        else{$('#legal_name_error').hide();GSTVals['legal_name'] = $('#legal_name').val()}

        if (!$('#reg_address').val()){valid=false;$('#reg_address_error').html('Required').show()}
        else{$('#reg_address_error').hide();GSTVals['reg_address'] = $('#reg_address').val()}

        if (!$('#shop_name').val()){valid=false;$('#shop_name_error').html('Required').show()}
        else{$('#shop_name_error').hide();GSTVals['shop_name'] = $('#shop_name').val()}

        if (!$('#gst_city').val()){valid=false;$('#gst_city_error').html('Required').show()}
        else{$('#gst_city_error').hide();GSTVals['gst_city'] = $('#gst_city').val()}

        if (!$('#gst_state_id').val()){valid=false;$('#gst_state_id_error').html('Required').show()}
        else{$('#gst_state_id_error').hide();GSTVals['gst_state_id'] = parseInt($('#gst_state_id option:selected').attr('id'))}

        if (!$('#gst_zip').val()){valid=false;$('#gst_zip_error').html('Required').show()}
        else{$('#gst_zip_error').hide();GSTVals['gst_zip'] = $('#gst_zip').val()}

        if (!$('#mobile').val()){valid=false;$('#mobile_error').html('Required').show()}
        else{$('#mobile_error').hide();GSTVals['gst_mobile'] = $('#mobile').val()}

        if (valid){
                ajax.jsonRpc('/gst/add',"call", GSTVals).then(function(result){
                    location.reload();
                })
            }

    })
    /* Add GSTIN ends */

    /* Add bank modal starts */
        $('#bank-details #delete_bank').click(function(){
            swal({
              title: "Are you sure want to delete it?",
              text: "Once deleted, you will not be able to recover this bank details!",
              icon: "warning",
              buttons: true,
              dangerMode: true,
            })
            .then((willDelete) => {
              if (willDelete) {
                    rpc.query({
                        model: 'res.partner.bank',
                        method: 'unlink',
                        args: [parseInt($(this).attr('partner-bank-id'))],
                    }).then(function(){
                        swal("Success!", "Successfully deleted!", "success").then(function(){
                            window.location.href = "/my/banks?tab=others";
                        });
                    });
              } else {
                swal("Bank details are not deleted!");
              }
            });
        })

        $('#modal_bank_details #bank_attachment').change(encodeImageFileAsURL(function(base64Img){
            $('#modal_bank_details #bank_attachment_base64').val(base64Img.replace(/^data:.+;base64,/, ''));
            //.css('background-image', 'url('+base64Img +')').hide().fadeIn(650);
        }));

        $('#modal_bank_details #acc_holder_name').change(function(){
            if (!$(this).val()){$('#modal_bank_details #acc_holder_name_error').html('Please enter beneficiary name.').show()}
            else{$('#modal_bank_details #acc_holder_name_error').hide()}
        })
        $('#modal_bank_details #acc_no').change(function(){
            if (!$(this).val()){$('#modal_bank_details #acc_no_error').html('Please enter account number.').show()}
            else if (!$.isNumeric($(this).val())){$('#modal_bank_details #acc_no_error').html('Please enter valid account number.').show()}
            else{$('#modal_bank_details #acc_no_error').hide()}
        })
        $('#modal_bank_details #confirm_acc_no').change(function(){
            if (!$(this).val()){$('#modal_bank_details #confirm_acc_no_error').html('Please enter confirm account number.').show()}
            else if (!$.isNumeric($(this).val())){$('#modal_bank_details #acc_no_error').html('Please enter valid account number.').show()}
            else if ($('#modal_bank_details #acc_no').val() != $(this).val()){$('#modal_bank_details #confirm_acc_no_error').html('Account number mismatch.').show()}
            else{$('#modal_bank_details #confirm_acc_no_error').hide()}
        })
        $('#modal_bank_details #bank_name').change(function(){
            if (!$(this).val()){$('#modal_bank_details #bank_name_error').html('Please enter bank name.').show()}
            else{$('#modal_bank_details #bank_name_error').hide()}
        })
        $('#modal_bank_details #ifsc_code').change(function(){
            if (!$(this).val()){$('#modal_bank_details #ifsc_code_error').html('Please enter IFSC code.').show()}
            else{$('#modal_bank_details #ifsc_code_error').hide()}
        })
        $('#modal_bank_details #bank_address').change(function(){
            if (!$(this).val()){$('#modal_bank_details #bank_address_error').html('Please enter bank address.').show()}
            else{$('#modal_bank_details #bank_address_error').hide()}
        })
        $('#modal_bank_details #bank_attachment').change(function(){
            if (!$(this).val()){$('#modal_bank_details #bank_attachment_error').html('Please attach required document.').show()}
            else{$('#modal_bank_details #bank_attachment_error').hide()}
        })

        $('#modal_bank_details #add_bank').click(function(){
            var BankDetails = {'is_default': $('#modal_bank_details #is_default').is(':checked')}
            var valid = true
            if ($('#modal_bank_details #acc_holder_name').val()){BankDetails['acc_holder_name']=$('#modal_bank_details #acc_holder_name').val()}
            else{valid=false;$('#modal_bank_details #acc_holder_name_error').html('Please enter beneficiary name.').show()}

            if ($('#modal_bank_details #acc_no').val()){BankDetails['acc_number']=$('#modal_bank_details #acc_no').val()}
            else{valid=false;$('#modal_bank_details #acc_no_error').html('Please enter account number.').show()}

            if (!($('#modal_bank_details #confirm_acc_no').val() && $('#modal_bank_details #acc_no').val() == $('#modal_bank_details #confirm_acc_no').val()))
                {valid=false;$('#modal_bank_details #confirm_acc_no_error').html('Please enter confirm account number.').show()}

            if ($('#modal_bank_details #bank_name').val()){BankDetails['bank_name']=$('#modal_bank_details #bank_name').val()}
            else{valid=false;$('#modal_bank_details #bank_name_error').html('Please enter bank name.').show()}

            if ($('#modal_bank_details #ifsc_code').val()){BankDetails['ifsc_code']=$('#modal_bank_details #ifsc_code').val()}
            else{valid=false;$('#modal_bank_details #ifsc_code_error').html('Please enter IFSC code.').show()}

            if ($('#modal_bank_details #bank_address').val()){BankDetails['bank_address']=$('#modal_bank_details #bank_address').val()}
            else{valid=false;$('#modal_bank_details #bank_address_error').html('Please enter bank address.').show()}

            if ($('#modal_bank_details #bank_attachment').val()){
                BankDetails['bank_attachment_name']=$('#modal_bank_details #bank_attachment').val()
                BankDetails['bank_attachment_base64']=$('#modal_bank_details #bank_attachment_base64').val()
            }
            else{valid=false;$('#modal_bank_details #bank_attachment_error').html('Please attach required document.').show()}

            if (! $('#modal_bank_details #agree_terms').is(":checked")){valid=false;}

            if (valid){
                ajax.jsonRpc('/bank/add',"call", BankDetails).then(function(result){
                    window.location.href = "/my/banks?tab=others";
                })
            }
        })

    $("#agree_terms").click(function () {
        if ($(this).is(":checked")) {
            $('#add_bank').prop('disabled', false);
        } else {
            $('#add_bank').prop('disabled', true);
        }
    });
    /* Add bank modal ends */

    // modal images show while click on image
    var popupModalShow = document.getElementById("popupModalShow");
    var showImg;
    var modalImg = document.getElementById("modalImg");
    $('.imageShowClick').click(function(){
        var id = $(this).attr('id');
        showImg = document.getElementById(id);
        popupModalShow.style.display = "block";
        modalImg.src = this.src;
    })
    var closeModal = document.getElementsByClassName("close-modal")[0];
    if(closeModal != null || closeModal != undefined){
        closeModal.onclick = function() {
          popupModalShow.style.display = "none";
        }
    }

     /* Read Notifications starts */
    $('.bs-read-notification').click(function(){
        $(this).removeClass('unread').addClass('read');
        var URL = $(this).attr('url')
        var NotificationID = $(this).attr('nt-id')
        ajax.jsonRpc('/read/notification',"call", {'notification_id': NotificationID}).then(function(res){
            if (res != false){
                window.location = URL
            }
            else{
                swal("OOPS!", `Something went wrong.`, "error");
            }
        })
    });
    /* Read Notifications ends */
});
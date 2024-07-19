odoo.define('builderbay.bs_signup_login', function(require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var rpc = require("web.rpc");
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var publicWidget = require('web.public.widget');
    var QWeb = core.qweb;
    var _t = core._t;
    var Widget = require('web.Widget');
    const wUtils = require('website.utils');

    var EmailRegex = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
    var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
    var GSTRegex = /^([0][1-9]|[1-2][0-9]|[3][0-7])([a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}[1-9a-zA-Z]{1}[zZ]{1}[0-9a-zA-Z]{1})+$/;
    var PANRegex = /^[A-Z]{3}[ABCFGHLJPT][A-Z][0-9]{4}[A-Z]$/;
    var AllCharsRegex = /^[ A-Za-z]+$/;
    var AllNumericRegex= /^[0-9]+$/;
    var AlphanumericRegex = /^[a-zA-Z0-9]$/;

    //SIGNUP ADDRESS
    publicWidget.registry.defaultAddress = publicWidget.Widget.extend({
        selector: '#signup-default-address',
        events: {
            'change #default-pincode':  '_onChangePincode',
            'change #default-city': '_onchangeCity',

            'click #addDefaultSignupAddress': '_onSubmitForm',
        },
        init: function() {
            this._super.apply(this, arguments);
        },
        _onChangePincode: function(e){
            var Pincode = e.target.value
            if ((Pincode.length < 6) || (!AllNumericRegex.test(Pincode))) {
                $("#"+ e.target.id +"-error").html("Please enter a valid pincode.").show();
            } else {
                $("#"+ e.target.id +"-error").html("").hide();
            }
        },
        _onchangeCity: function(e){
            var City = e.target.value
            if ((City.length == 0) || (!AllCharsRegex.test(City))) {
                $("#"+ e.target.id +"-error").html("Please enter a valid city name.").show();
            } else {
                $("#"+ e.target.id +"-error").html("").hide();
            }
        },
        _onSubmitForm: function(e){
            if ($('#signup-default-address #default-sitename').val() &&
                $('#signup-default-address #default-mobilenumber').val() &&
                $('#signup-default-address #default-pincode').val() &&
                $('#signup-default-address #default-street1').val() &&
                $('#signup-default-address #default-street2').val() &&
                $('#signup-default-address #default-landmark').val() &&
                $('#signup-default-address #default-city').val() &&
                $('#signup-default-address #default-district option:selected').attr('id') &&
                $('#signup-default-address #default-state option:selected').attr('id')){
                    $('#submit-error').html('').hide();
                    ajax.jsonRpc("/bs/default/address", 'call',
                        {'site_name': $('#signup-default-address #default-sitename').val(),
                         'mobile': $('#signup-default-address #default-mobilenumber').val(),
                         'zip': $('#signup-default-address #default-pincode').val(),
                         'street': $('#signup-default-address #default-street1').val(),
                         'street2': $('#signup-default-address #default-street2').val(),
                         'landmark': $('#signup-default-address #default-landmark').val(),
                         'city': $('#signup-default-address #default-city').val(),
                         'district_id': parseInt($('#signup-default-address #default-district option:selected').attr
                         ('id')),
                         'state_id': parseInt($('#signup-default-address #default-state option:selected').attr('id'))})
                    .then(function (res) {
                        if (res == true){location.reload(true)}
                    });
            }
            else{
                $('#signup-default-address #submit-error').html('Please fill in all values.').show();
                return false
            }
        },
    });

    // SIGNUP - b2b, b2c checks
    $('#b2b').change(function() {
        if ($(this).is(":checked")) { $('#b2c').prop('checked',false);
                                    $('#b2c-signup-add').hide();
                                    $('#b2b-signup-div').show(); }
        else { $('#b2c').prop('checked',true);
            $('#b2c-signup-add').show();
            $('#b2b-signup-div').hide(); }
    });
    $('#b2c').change(function() {
        if ($(this).is(":checked")) {$('#b2b').prop('checked',false);
                                    $('#b2b-signup-div').hide();
                                    $('#b2c-signup-add').show();}
        else {$('#b2b').prop('checked',true);
                $('#b2b-signup-div').show();
                $('#b2c-signup-add').hide(); }
    });

    $(".inline_input, .accpetNumber").keypress(function (e) {
       if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57)) {
         return false;
      }
    });


    //########################### GENERIC #######################

    $( document ).ready(function()
        {
            function ControlSignupStates(District, EleID){
                ajax.jsonRpc('/signup/states',"call", {'DistrictID':District}).then(function(State){
                    if(EleID == 'district_id'){
                        $('#state_id option').each(function(e){
                            if (parseInt($(this).val()) == State){
                                $(this).prop('selected',true);
                            }
                       })
                       $('#state_id').trigger('chosen:updated');
                    }else{
                        $('#gst_state_id option').each(function(e){
                            if (parseInt($(this).val()) == State){
                                $(this).prop('selected',true);
                            }
                       })
                       $('#gst_state_id').trigger('chosen:updated');
                    }
                })
            }
            function ControlSignupDistricts(State, EleID){
                if(EleID == 'state_id'){
                    $('#district_id option').each(function(e){
                        $(this).show();
                    })
                }else{
                    $('#gst_district_id option').each(function(e){
                        $(this).show();
                    })
                }
                ajax.jsonRpc('/signup/districts',"call", {'StateID':State}).then(function(Districts){
                    if(EleID == 'state_id'){
                        $('#district_id option').each(function(e){
                            if ($.inArray(parseInt($(this).val()), Districts) ==-1){
                                if($(this).val() != '0'){
                                    $(this).hide();
                                }
                                $('#district_id').val('0');
                                // $("#district_id option[value='0']").attr('selected', 'selected');
                            }
                       })
                       $('#district_id').trigger('chosen:updated');
                    }else{
                        $('#gst_district_id option').each(function(e){
                            if ($.inArray(parseInt($(this).val()), Districts) ==-1){
                                if($(this).val() != '0'){
                                    $(this).hide();
                                }
                                $('#gst_district_id').val('0');
                                // $("#gst_district_id option[value='0']").attr('selected', 'selected');
                            }
                       })
                       $('#gst_district_id').trigger('chosen:updated');
                    }
                })
            }
            function DisplayInputError(Value, EleID, Regex, Label){
                if (!Value) {$('#error_' + EleID).show();}
                else if (Regex && !Regex.test(Value)) {
                    $('#error_' + EleID).html('Please enter a valid '+ Label).show();
                }else if(Label == 'mobile.'){
                    if(Value.length < 10){
                        $('#error_' + EleID).html('Please enter a valid '+ Label).show();
                    }else{
                        $('#error_' + EleID).hide();
                    }
                }
                else {
                    $('#error_' + EleID).hide();
                    if (Label == 'state.'){
                        ControlSignupDistricts(Value, EleID);
                    }
                    if (Label == 'district.'){
                        ControlSignupStates(Value, EleID);
                    }
                }


            }

            $(".signupIndCustomer #confirm_password").keyup(checkPasswordMatch);
            function checkPasswordMatch() {
                $(".signupIndCustomer #CheckPasswordMatch").html("");
                var password = $('.signupIndCustomer #password').val();
                if(password == ""){
                    $("#error_confirm_password").html("Please confirm password.").show();
                }else if(password.length < 6){
                    $("#error_confirm_password").html("").hide();
                    $(".signupIndCustomer #CheckPasswordMatch").html("You have to enter at least 6 characters.")
                }else{
                    $("#error_confirm_password").html("").hide();
                }
                var confirm_password = $('.signupIndCustomer #confirm_password').val();
                if (password != confirm_password) {
                    $("#CheckPasswordMatch").html("Passwords does not match!");
                    $("#CheckedPasswordMatch").html("");
                }
                else {
                    $("#CheckedPasswordMatch").html("Passwords match.");
                    $("#CheckPasswordMatch").html("");
                }
            }
            $(".signupIndCustomer #password").keyup(PasswordCheckLength);
            function PasswordCheckLength(){
                var passwordLength = $(".signupIndCustomer #password").val();
                if(passwordLength == ""){
                    $('#error_password').html('Please enter your password.').show();
                }else if(passwordLength.length < 6){
                    $('#error_password').html('You have to enter at least 6 characters.').show();
                }else {
                    $('#error_password').html('').hide();
                }
            }

            $('#email').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), EmailRegex, 'email.')})
            $('#mobile').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), MobileRegex, 'mobile.') })

            $('#fname').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllCharsRegex, 'first name.') })
            $('#lname').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllCharsRegex, 'last name.') })
            $('#city').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllCharsRegex, 'city.') })
            $('#state_id').change(function(){
                DisplayInputError($(this).val(), $(this).attr('id'), AllNumericRegex, 'state.');
            })
            $('#district_id').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllNumericRegex, 'district.') })
            $('#zip').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllNumericRegex, 'pincode.') })

            $('#pan').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), PANRegex, 'PAN') })
            $('#legal_name').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), false, 'trade name.') })
            $('#shop_name').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), false, 'shop name.') })
            $('#gst_city').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllCharsRegex, 'city.') })
            $('#gst_state_id').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllNumericRegex, 'state.') })
            $('#gst_district_id').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllNumericRegex, 'district.') })
            $('#gst_zip').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), AllNumericRegex, 'pincode.') })
            $('#reg_address').change(function(){ DisplayInputError($(this).val(), $(this).attr('id'), false, 'registered address.') })

            $('#gstin').change(function(){
                if ($(this).val() && window.location.href.indexOf("/upload/enquiry") <= -1){
                    if (GSTRegex.test($(this).val())){
                        var GST = $(this).val();
                        $('#error_gstin').hide()
                        ajax.jsonRpc('/bs/gst/verify',"call", {'gstin':$(this).val()}).then(function(res){
                            $('#pan').val(GST.slice(2, 12));$('#pan').prop('readonly','1');

                            if (res != false){
                                if (res['reg_add']) {$('#reg_address').val(res['reg_add']); $('#reg_address').prop('readonly','1')}
                                if (res['state']) {
                                    ControlSignupDistricts(res['state'], 'gst_state_id')
                                }
                                if (res['district']) {
                                    ControlSignupStates(res['district'], 'gst_district_id')
                                }
                                if (res['pincode']) {$('#gst_zip').val(res['pincode']).change(); $('#gst_zip').prop('readonly','1')}
                                if (res['city']) {$('#gst_city').val(res['city']).change(); $('#gst_city').prop('readonly','1')}
                                if (res['trade_name']) {$('#shop_name').val(res['trade_name']).change(); $('#shop_name').prop('readonly','1')}
                                if (res['legal_name']) {$('#legal_name').val(res['legal_name']).change(); $('#legal_name').prop('readonly','1')}
                                /* Other validations - manage gst page */
                                $('#reg_address').change()

                            }
                            //else {
                            //    $('#error_gstin').html('Please recheck GSTIN').show();
                            //    $('#gstin_error').html('Please recheck GSTIN').show()}
                        })
                    }
                    else { $('#error_gstin').html('Please enter valid GSTIN').show()}
                }
                else{$('#error_gstin').html('Please enter GSTIN').show()}
            })
            let timerOn = true;
            let timerOn2 = true;

            function timer(remaining) {
              var m = Math.floor(remaining / 60);
              var s = remaining % 60;
              m = m < 10 ? '0' + m : m;
              s = s < 10 ? '0' + s : s;
              if(document.getElementById('timer').innerHTML != undefined){
                  document.getElementById('timer').innerHTML = s;
              }
              remaining -= 1;
              if(remaining >= 0 && timerOn) {
                setTimeout(function() {
                    timer(remaining);
                }, 1000);
                return;
              }
              if(!timerOn) {
                // Do validate stuff here
                return;
              }
            }
            function timer2(remaining) {
              var m = Math.floor(remaining / 60);
              var s = remaining % 60;
              m = m < 10 ? '0' + m : m;
              s = s < 10 ? '0' + s : s;
              if(document.getElementById('timer-phone').innerHTML != undefined){
                  document.getElementById('timer-phone').innerHTML = s;
              }
              remaining -= 1;
              if(remaining >= 0 && timerOn2) {
                setTimeout(function() {
                    timer2(remaining);
                }, 1000);
                return;
              }
              if(!timerOn2) {
                // Do validate stuff here
                return;
              }
            }

                //---------------------------------- SEND SIGNUP OTPs ------------------------------------------
            $('.oe_signup_form #send_email_otp').click(function(){
                $("#error_email").html('').hide();
                var Email = $('#email').val();

                if (Email != ''){
                    var eml = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
                    if (eml.test(Email) == false) {
                        $("#error_email").html("Please enter valid email address.").show();
                    } else {
                        $("#error_email").hide();
                        $("#send_email_otp").hide();
                        $("#show-email-loading").show();
                        ajax.jsonRpc('/send/signup/otp',"call", {'login':Email,
                                                            'type':'email',
                                                            'otp_type': 'signup'}).then(function(result){
                           if (result['error'] != ''){
                            $("#error_email").html(result['error']).show();
                                $("#send_email_otp").show();
                                $("#show-email-loading").hide();
                           }
                           else { $("#verify_signup_email_otp").show();
                                $("#show-email-loading").hide();
                                $("#otp-msg-email").show();
                                timer(30);
                                setTimeout(function(){
                                    if($('#email-verified').css('display') == 'none'){
                                        $("#otp-msg-email").hide();
                                        $("#send_email_otp").show();
                                        $('.oe_signup_form #send_email_otp').html('Resend OTP');
                                        $('#show-email-loading').html('<i class="fa fa-spinner fa-spin loading-fa"></i> Resend OTP');
                                    }
                                }, 30000);
                                $('#email').addClass('verified'); }
                        })
                    }
                }
                else {
                    $("#error_email").html('Please enter your email.').show();
                }
            })
            $('.oe_signup_form #send_mobile_otp').click(function(){
                $("#error_mobile").html('').hide();
                var Mobile = $('#mobile').val();
                if (Mobile != ''){
                    var intRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
                    if (intRegex.test(Mobile)) {
                        if ((Mobile.length < 10) || (!intRegex.test(Mobile))) {
                            $("#error_mobile").html("Please enter a valid mobile number.").show();
                        } else {
                        $("#error_mobile").hide();
                        $("#send_mobile_otp").hide();
                        $("#show-phone-loading").show();
                        ajax.jsonRpc('/send/signup/otp',"call", {'login': Mobile,
                                                        'type': 'mobile',
                                                        'otp_type': 'signup'}).then(function(result){
                       if (result['error'] != ''){
                        $("#error_mobile").html(result['error']).show();
                        $("#send_mobile_otp").show();
                        $("#show-phone-loading").hide();
                        }
                       else { $("#verify_signup_mobile_otp").show();
                             $("#show-phone-loading").hide();
                            $("#otp-msg-phone").show();
                            $("#send_mobile_otp").hide();
                            timer2(30);
                            setTimeout(function(){
                                if($('#mobile-verified').css('display') == 'none'){
                                    $("#otp-msg-phone").hide();
                                    $("#send_mobile_otp").show();
                                    $('.oe_signup_form #send_mobile_otp').html('Resend OTP');
                                    $('#show-phone-loading').html('<i class="fa fa-spinner fa-spin loading-fa"></i> Resend OTP');
                                }
                            }, 30000);
                           $('#mobile').addClass('verified'); }
                    })
                    }
                    }
                }
                else {
                    $("#error_mobile").html('Please enter your mobile number.').show();
                }
            })

            //---------------------------------- VERIFY SIGNUP OTPs ------------------------------------------
            $('#verify_email_otp').click(function(){
                var EmailOTP = ''
                $('#email_otp :input').each(function(){EmailOTP += $(this).val()})
                $("#email_otp_failed").hide()
                if (EmailOTP != ''){
                    $('#verify_email_otp').hide();
                    $('#verify_email_loading').show();
                    ajax.jsonRpc('/bs/validate/otp',"call", {'otp': EmailOTP}).then(function(result){
                        $('#verify_email_loading').hide();
                        $('#verify_email_otp').show();
                       if (result != false){
                            $('#email-verified').show();
                            $("#error_email").html("").hide();
                            $('#verify_signup_email_otp').hide();
                            $('#email').prop('readonly','1');
                            $('.oe_signup_form #send_email_otp').hide();
                            $("#show-email-loading").hide();
                            $("#otp-msg-email").hide();
                       }
                       else{ $('#email_otp_failed').html('OTP Failed').show()}
                    })
                }
                else { $("#email_otp_failed").html('Please enter OTP.').show() }
            })
            $('#verify_mobile_otp').click(function(){
                var MobileOTP = ''
                $('#mobile_otp :input').each(function(){MobileOTP += $(this).val()})
                $('#mobile_otp_failed').hide()
                if (MobileOTP != ''){
                    $('#verify_mobile_otp').hide();
                    $('#verify_mobile_loading').show();
                    ajax.jsonRpc('/bs/validate/otp',"call", {'otp': MobileOTP}).then(function(result){
                        $('#verify_mobile_otp').show();
                    $('#verify_mobile_loading').hide();
                       if (result != false){
                           $('#mobile-verified').show();
                           $("#error_mobile").html("").hide();
                           $('#verify_signup_mobile_otp').hide();
                           $('#mobile').prop('readonly','1');
                           $('.oe_signup_form #send_mobile_otp').hide();
                           $("#show-phone-loading").hide();
                            $("#otp-msg-phone").hide();
                       }
                       else{ $('#mobile_otp_failed').html('OTP Failed').show()}
                    })
                }
                else { $("#mobile_otp_failed").html('Please enter OTP.').show() }
            })

            // ---------------OTP next box activity : TODO: CHECK ------------------
            $('.SignupEmailOTP').on('keyup', function (e) {
              var key = event.keyCode || event.charCode;
              if( key === 8 || key === 46 ){ /* for backspace, will move to the previous box */
                 $(this).prev('input').focus();
                 return;
              } $(this).next('input').focus();
            });
            $('.SignupMobileOTP').on('keyup', function (e) {
              var key = event.keyCode || event.charCode;
              if( key === 8 || key === 46 ){/* for backspace, will move to the previous box */
                 $(this).prev('input').focus();
                 return;
              } $(this).next('input').focus();
            });
        });
    // ######################### GENERIC ##########################

    // ############################################## SIGNUP ###########################################
    let timerOn3 = true;
    function timer3(remaining) {
              var m = Math.floor(remaining / 60);
              var s = remaining % 60;
              m = m < 10 ? '0' + m : m;
              s = s < 10 ? '0' + s : s;
              if(document.getElementById('timer-phone-email-signup').innerHTML != undefined){
                  document.getElementById('timer-phone-email-signup').innerHTML = s;
              }
              remaining -= 1;
              if(remaining >= 0 && timerOn3) {
                setTimeout(function() {
                    timer3(remaining);
                }, 1000);
                return;
              }
              if(!timerOn3) {
                // Do validate stuff here
                return;
              }
            }
    $("#emailPhoneSignupError, .verificationCode").hide();
    $('#otpBtnSignup').click(function() {
        $("#emailPhoneSignupError").html('').hide();
        var phone_emailval = $('#emailPhoneSignup').val();
        var intRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if (intRegex.test(phone_emailval)) {
            if ((phone_emailval.length < 10) || (!intRegex.test(phone_emailval))) {
                $("#emailPhoneSignupError").html("Please enter a valid mobile number.").show();
            } else {
                $("#emailPhoneSignupError").hide();
                $("#otpBtnSignup").hide();
                $("#show-signup-otp").show();
                //do signup logic here if user coming with phone
                ajax.jsonRpc('/send/signup/otp',"call", {'login':phone_emailval,
                                                    'type':'mobile',
                                                    'otp_type': 'signup'}).then(function(result){
                   if (result['error'] != ''){
                    $("#emailPhoneSignupError").html(result['error']).show();
                    $("#show-signup-otp").hide();
                    $("#otpBtnSignup").show();
                    }
                   else {   $('#mobile').val(phone_emailval).prop('readonly','1');
                            $(".verificationCode").show();
                            $("#otp-msg-phone-e-s").show();
                            $("#otpBtnSignup").hide();
                            $("#show-signup-otp").hide();
                            timer3(30);
                            setTimeout(function(){
                                $("#otp-msg-phone-e-s").hide();
                                $("#otpBtnSignup").show();
                                $("#show-signup-otp").html('<i class="fa fa-spinner fa-spin loading-fa"></i> Resend OTP');
                                $('#otpBtnSignup').html('Resend OTP');
                            }, 30000);

                        }
                })
            }
        } else if (phone_emailval.length < 1) {
            $("#emailPhoneSignupError").html("Please enter valid email address or valid mobile number.").show();
        } else {
            var eml = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
            if (eml.test(phone_emailval) == false) {
                $("#emailPhoneSignupError").html("Please enter valid email address.").show();
            } else {
                $("#emailPhoneSignupError").hide();
                // Send OTP to mail
                $("#otpBtnSignup").hide();
                $("#show-signup-otp").show();
                ajax.jsonRpc("/send/signup/otp", 'call', {'login': phone_emailval,
                                                      'type': 'email',
                                                      'otp_type': 'signup'})
                .then(function (res) {
                    if (res['error'] == '') {$('#email').val(phone_emailval).prop('readonly','1');
                            $(".verificationCode").show();
                            $("#otp-msg-phone-e-s").show();
                             $("#otpBtnSignup").hide();
                             $("#show-signup-otp").hide();
                            timer3(30);
                            setTimeout(function(){
                                $("#otp-msg-phone-e-s").hide();
                                $("#otpBtnSignup").show();
                                $("#show-signup-otp").html('<i class="fa fa-spinner fa-spin loading-fa"></i> Resend OTP');
                                $('#otpBtnSignup').html('Resend OTP');
                            }, 30000);
                            }
                    else {
                        $('#emailPhoneSignupError').html(res['error']).show();
                        $("#show-signup-otp").hide();
                        $("#otpBtnSignup").show();
                        }
                });
            }
        }
    });
    $("#continuebtnNext").click(function() {
        var hasOtpValue = false;
        $('.checkSignupOtp').each(function() {
            if ($(this).val()) { hasOtpValue = true; }
            else { hasOtpValue = false; return false; }
        });
        if (!hasOtpValue) {
            $("#SignupOTPError").html("Please enter all the fields.");
        } else {// call the signup OTP here
            $("#SignupOTPError").html("");
            var OTP = ''
            $('div.confirmation_code_group :input').each(function(){OTP += $(this).val()})
            $("#continuebtnNext").hide();
            $("#show-continue-loading").show();
            ajax.jsonRpc('/bs/validate/otp',"call", {'otp': OTP}).then(function(result){
                $("#continuebtnNext").show();
                $("#show-continue-loading").hide();
               if (result != false){$(".verificationCode, .otpForSignup").hide();
                                    $('form.oe_signup_form').show();
                                    $(".selectRole").show();
                                    $('.signupIndCustomer').show();

                                    if (!$('#mobile').val()) { $('.oe_signup_form #send_mobile_otp').show();
                                                                $('#mobile-verified').hide();
                                                                $('.oe_signup_form #mobile').removeClass('verified');}
                                    else{$('.oe_signup_form #send_mobile_otp').hide();
                                        $('#mobile-verified').show();
                                        $("#error_mobile").html("").hide();
                                        $('.oe_signup_form #mobile').addClass('verified');}

                                    if (!$('#email').val()) { $('.oe_signup_form #send_email_otp').show();
                                                                $('#email-verified').hide();
                                                                $('.oe_signup_form #email').removeClass('verified');}
                                    else{$('.oe_signup_form #send_email_otp').hide();
                                        $('#email-verified').show();
                                        $("#error_email").html("").hide();
                                        $('.oe_signup_form #email').addClass('verified');}
                                    }
               else{ $('#SignupOTPError').html('OTP Failed').show()}
            })
        }
    });

    //####### B2C ############
    $(".error_signup").hide();
    $("#SubmitBttn").click(function(event) {

        var valid = true,
        message = '';
        $('.oe_signup_form input:visible').each(function(){ //Input Fields
            if($(this).attr("name") == 'email'){ // email validation
                var emailVerified = document.getElementById("email-verified");
                var EmailRegex = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
                if($(this).val() == ""){
                    $('#error_email').html('Please enter your email.').show();
                    valid = false;
                }else if(EmailRegex.test($(this).val()) == false){
                    valid = false;
                    $("#error_email").html("Please enter valid email address.").show();
                }else if(window.getComputedStyle(emailVerified).display === "none"){
                    valid = false;
                    $("#error_email").html("Please verify email.").show();
                }else{
                    $("#error_email").html("").hide();
                }
            }
            if($(this).attr("name") == 'mobile'){ // phone validation
                var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
                var mobileVerified = document.getElementById("mobile-verified");
                if($(this).val() == ""){
                    valid = false;
                    $('#error_mobile').html('Please enter your mobile number.').show();
                }else if(!MobileRegex.test($(this).val()) || ($(this).val().length < 10)){
                    $("#error_mobile").html("Please enter valid mobile number.").show();
                    valid = false;
                }else if(window.getComputedStyle(mobileVerified).display === "none"){
                    valid = false;
                    $("#error_mobile").html("Please verify mobile.").show();
                }else{
                    $("#error_mobile").html("").hide();
                }
            }
            if($(this).attr("name") == 'fname'){
                var AllCharsRegex = /^[ A-Za-z]+$/;
                if($(this).val() == ""){
                    $('#error_fname').html('Please enter your first name.').show();
                    valid = false;
                }else if(AllCharsRegex.test($(this).val()) == false){
                    valid = false;
                    $('#error_fname').html('Please enter a valid first name.').show();
                }else {
                    $("#error_fname").html("").hide();
                }
            }
            if($(this).attr("name") == 'lname'){
                var AllCharsRegex = /^[ A-Za-z]+$/;
                if($(this).val() == ""){
                    $('#error_lname').html('Please enter your last name.').show();
                    valid = false;
                }else if(AllCharsRegex.test($(this).val()) == false){
                    valid = false;
                    $('#error_lname').html('Please enter a valid last name.').show();
                }else {
                    $("#error_lname").html("").hide();
                }
            }
            if($(this).attr("name") == 'password'){
                var passwordLength = $(this).val();
                if($(this).val() == ""){
                    $('#error_password').html('Please enter your password.').show();
                    valid = false;
                }else if(passwordLength.length < 6){
                    valid = false;
                    $('#error_password').html('You have to enter at least 6 characters.').show();
                }else {
                    $('#error_password').html('').hide();
                }
            }
            if($(this).attr("name") == 'confirm_password'){
                if($(this).val() == ""){
                    $('#error_confirm_password').html('Please confirm password.').show();
                    valid = false;
                }else if($("#CheckedPasswordMatch").html() == ""){
                    valid = false;
                }else {
                    $('#error_confirm_password').html('').hide();
                }
            }
            if($(this).attr("name") == 'zip'){
                var zipCodeLength = $(this).val();
                var AllNumericRegex= /^[0-9]+$/;
                if($(this).val() == ""){
                    $('#error_zip').html('Please enter your pincode.').show();
                    valid = false;
                }else if((zipCodeLength.length < 6) || (!AllNumericRegex.test(zipCodeLength))){
                    valid = false;
                    $('#error_zip').html("Please enter a valid pincode.").show();
                }else {
                    $('#error_zip').html('').hide();
                }
            }
            if($(this).attr("name") == 'city'){
                var AllCharsRegex = /^[ A-Za-z]+$/;
                var cityValue = $(this).val();
                if ((cityValue.length == 0)) {
                    $("#error_city").html("Please enter your city.").show();
                    valid = false;
                } else if((!AllCharsRegex.test(cityValue))){
                    valid = false;
                    $("#error_city").html("Please enter a valid city name.").show();
                }else {
                    $("#error_city").html("").hide();
                }
            }
            if($(this).attr("name") == 'gstin'){
                var GSTRegex = /^([0][1-9]|[1-2][0-9]|[3][0-7])([a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}[1-9a-zA-Z]{1}[zZ]{1}[0-9a-zA-Z]{1})+$/;
                var GSTValue = $(this).val();
                if($(this).val() == ""){
                    $('#error_gstin').html('Please enter GSTIN.').show();
                    valid = false;
                }else if((!GSTRegex.test(GSTValue))){
                    valid = false;
                    $('#error_gstin').html("Please enter a valid GSTIN.").show();
                }else {
                    $('#error_gstin').html('').hide();
                }
            }
            if($(this).attr("name") == 'pan'){
                var PANRegex = /^[A-Z]{3}[ABCFGHLJPT][A-Z][0-9]{4}[A-Z]$/;
                var PANValue = $(this).val();
                if($(this).val() == ""){
                    $('#error_pan').html('Please enter PAN.').show();
                    valid = false;
                }else if((!PANRegex.test(PANValue))){
                    valid = false;
                    $('#error_pan').html("Please enter a valid PAN.").show();
                }else {
                    $('#error_pan').html('').hide();
                }
            }
            if($(this).attr("name") == 'shop_name'){
                if($(this).val() == ""){
                    $('#error_shop_name').html('Please enter your company name.').show();
                    valid = false;
                }else {
                    $('#error_shop_name').html('').hide();
                }
            }
            if($(this).attr("name") == 'legal_name'){
                if($(this).val() == ""){
                    $('#error_legal_name').html('Please enter your legal name.').show();
                    valid = false;
                }else {
                    $('#error_legal_name').html('').hide();
                }
            }
            if($(this).attr("name") == 'gst_zip'){
                var pinCodeLength = $(this).val();
                var AllNumericRegex= /^[0-9]+$/;
                if($(this).val() == ""){
                    $('#error_gst_zip').html('Please enter your pincode.').show();
                    valid = false;
                }else if((pinCodeLength.length < 6) || (!AllNumericRegex.test(pinCodeLength))){
                    valid = false;
                    $('#error_gst_zip').html("Please enter a valid pincode.").show();
                }else {
                    $('#error_gst_zip').html('').hide();
                }
            }
            if($(this).attr("name") == 'gst_city'){
                var AllCharsRegex = /^[ A-Za-z]+$/;
                var cityValue = $(this).val();
                if ((cityValue.length == 0)) {
                    $("#error_gst_city").html("Please enter your city.").show();
                    valid = false;
                } else if((!AllCharsRegex.test(cityValue))){
                    valid = false;
                    $("#error_gst_city").html("Please enter a valid city name.").show();
                }else {
                    $("#error_gst_city").html("").hide();
                }
            }
        })

        $('textarea:visible').each(function(){ //text area Fields
            if($(this).attr("name") == 'reg_address'){
                if($(this).val() == ""){
                    valid = false;
                    $('#error_reg_address').html('Please enter your registered address.').show();
                }else {
                    $('#error_reg_address').html('').hide();
                }
            }
        })

        if($(".signupBusCustomer").is(":visible")){
            // Customer role: ex:dealer etc
            var group = document.signupForm.cusrole;
            for (var iC=0; iC<group.length; iC++) {
            if (group[iC].checked)
            break;
            }
            if (iC==group.length){
                $('#error_user_role').html('Please select at least one role.').show();
                valid = false;
            }else{
                $('#error_user_role').html('').show();
            }

            if($("#gst_district_id").attr("name") == 'gst_district_id'){
                if (!$("#gst_district_id").val()){
                    $("#error_gst_district_id").html("Please select district.").show();
                    valid=false;
                }else{
                    $("#error_gst_district_id").html("").hide();
                }
            }
            if($("#gst_state_id").attr("name") == 'gst_state_id'){
                if (!$("#gst_state_id").val()){
                    $("#error_gst_state_id").html("Please select state.").show();
                    valid=false;
                }else{
                    $("#error_gst_state_id").html("").hide();
                }
            }
        }else{
            if($("#district_id").attr("name") == 'district_id'){
                if (!$("#district_id").val()){
                    $("#error_district_id").html("Please select district.").show();
                    valid=false;
                }else{
                    $("#error_district_id").html("").hide();
                }
            }
            if($("#state_id").attr("name") == 'state_id'){
                if (!$("#state_id").val()){
                    $("#error_state_id").html("Please select state.").show();
                    valid=false;
                }else{
                    $("#error_state_id").html("").hide();
                }
            }
        }
        if (valid) {
            $('#signup-error-msg').html('').hide();
            if (event.originalEvent != undefined) {
               $("#saveAddress").show();
               $('form.oe_signup_form #redirect').val(sessionStorage['RedirectingURL']);
               sessionStorage.removeItem('RedirectingURL');
               $('form.oe_signup_form').submit();
            }
        }
    });

    // ####### B2C ############

    // ############## B2B ###########
    $('.signupBusCustomer input').keyup(function() {
        if ($(this).attr('id') != 'gstin'){$("#SubmitBttn").click();}
        // else GSTIN API will be triggered
    });
    $(".signupBusCustomer #confirm_password").keyup(checkBPasswordMatch);
    function checkBPasswordMatch() {
        $(".signupBusCustomer #CheckPasswordMatch").html("");
        var password = $('.signupBusCustomer #password').val();
        if (password.length < 8){$(".signupBusCustomer #CheckPasswordMatch").html("Min 8 char long!")}
        var confirm_password = $('.signupBusCustomer #confirm_password').val();
        if (password != confirm_password) {
            $(".signupBusCustomer #CheckPasswordMatch").html("Passwords does not match!");
            $(".signupBusCustomer #CheckedPasswordMatch").html("");
        } else {
            $(".signupBusCustomer #CheckedPasswordMatch").html("Passwords match.");
            $(".signupBusCustomer #CheckPasswordMatch").html("");
        }
    }
    // ############# B2B ###########

    //###################ADDRESS############

    // ############################################## SIGNUP ###########################################

    let timerOn4 = true;
    function timer4(remaining) {
              var m = Math.floor(remaining / 60);
              var s = remaining % 60;
              m = m < 10 ? '0' + m : m;
              s = s < 10 ? '0' + s : s;
              if(document.getElementById('timer-phone-email-signin').innerHTML != undefined){
                  document.getElementById('timer-phone-email-signin').innerHTML = s;
              }
              remaining -= 1;
              if(remaining >= 0 && timerOn4) {
                setTimeout(function() {
                    timer4(remaining);
                }, 1000);
                return;
              }
              if(!timerOn4) {
                // Do validate stuff here
                return;
              }
            }
    // ############################################## LOGIN ###########################################
    //$("#loginVarificationCode").hide();
    $('#otpBtnSignin').click(function() {
        $('#LoginOTPError').html('').hide();
        var LoginVal = $('#emailPhoneSignin').val();
        var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if (MobileRegex.test(LoginVal)) {
            if ((LoginVal.length < 10) || (!MobileRegex.test(LoginVal))) {
                $("#emailPhoneSigninError").html("Please enter a valid mobile number.").show();
            } else {
                $("#emailPhoneSigninError").hide();
                $("#otpBtnSignin").hide();
                $("#show-login-getOTP").show();

                //do signin logic here if user coming with phone
                ajax.jsonRpc('/send/login/otp',"call", {'login':LoginVal,
                                                    'type':'mobile',
                                                    'otp_type': 'login'}).then(function(result){
                   if (result['uid'] != false){
                        $("#show-login-getOTP").hide();
                        $('#bs-uid').val(result['uid']);
                        $("#loginVarificationCode").show();
                        $("#otp-msg-phone-e-signin").show();
                            $("#otpBtnSignin").hide();
                            timer4(30);
                            setTimeout(function(){
                                $("#otp-msg-phone-e-signin").hide();
                                $("#otpBtnSignin").show();
                                $('#otpBtnSignin').html('Resend OTP');
                                $("#show-login-getOTP").html('<i class="fa fa-spinner fa-spin loading-fa"></i> Resend OTP');
                            }, 30000);
                    }
                   else {
                        $("#otpBtnSignin").show();
                        $("#show-login-getOTP").hide();
                        $('#emailPhoneSigninError').html(result['error']).show()
                   }
                })
            }
        } else if (LoginVal.length < 1) {
            $("#emailPhoneSigninError").show();
            $("emailPhoneSigninError").html("Please enter valid email address or valid mobile number.");
        } else {
            var EmailRegex = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
            if (EmailRegex.test(LoginVal) == false) {
                $("#emailPhoneSigninError").html("Please enter valid email address.").show();
            } else {// Login with OTP - Email - send OTP
                $("#emailPhoneSigninError").hide();
                $("#otpBtnSignin").hide();
                $("#show-login-getOTP").show();
                ajax.jsonRpc('/send/login/otp',"call", {'login':LoginVal,
                                                    'type':'email',
                                                    'otp_type': 'login'}).then(function(result){

                   if (result['uid'] != false){
                        $("#show-login-getOTP").hide();
                        $('#bs-uid').val(result['uid']);
                        $("#loginVarificationCode").show();
                        $("#otp-msg-phone-e-signin").show();
                        $("#otpBtnSignin").hide();
                            timer4(30);
                            setTimeout(function(){
                                $("#otp-msg-phone-e-signin").hide();
                                $("#otpBtnSignin").show();
                                $('#otpBtnSignin').html('Resend OTP');
                                $("#show-login-getOTP").html('<i class="fa fa-spinner fa-spin loading-fa"></i> Resend OTP');
                            }, 30000);
                    }
                   else {
                    $("#otpBtnSignin").show();
                    $("#show-login-getOTP").hide();
                    $('#emailPhoneSigninError').html(result['error']).show()
                    }
                })
            }
        }
    });
    $("#submitLoginWithOTP").click(function() {
        var hasOtpValue = false;
        $('.checkSigninOtp').each(function() {
            if ($(this).val()) { hasOtpValue = true; }
            else { hasOtpValue = false; return false; }
        });
        if (!hasOtpValue) {
            $("#LoginOTPError").html("Please enter all the fields.");
        } else {// call the login OTP here
            $("#LoginOTPError").html("");
            var OTP = ''
            $('div.confirmation_code_group :input').each(function(){OTP += $(this).val()})
            $("#show-login-otp").show();
            $("#submitLoginWithOTP").hide();
            ajax.jsonRpc('/bs/validate/otp',"call", {'otp': OTP}).then(function(result){
                $("#show-login-otp").hide();
                $("#submitLoginWithOTP").show();
                if (result){
                    $('form.oe_login_form').attr('action',$('form.oe_login_form').attr('action')+"?redirect="+sessionStorage['RedirectingURL'])
                    sessionStorage.removeItem('RedirectingURL');
                    $('form.oe_login_form').submit();
                }
                else{
                    $("#LoginOTPError").html('OTP Failed !').show();
                }
            })
        }
    });
    $("#emailPhoneError, #passwordError").hide();
    $("#password").keyup(function(event) {
        if (event.keyCode === 13) {
            $("#submitLoginWithEP").click();
        }
    });
    $('#resetEmailPhone').bind('input', function() {
        setTimeout(function(){
            resetEmailPhone();
        }, 100);
    });
    $('#resetName').bind('input', function() {
        setTimeout(function(){
            resetName();
        }, 100);
    });
    $('#resetPassword').bind('input', function() {
        setTimeout(function(){
            PasswordNewCheckLength();
        }, 100);
    });
    $('#resetConfirmPassword').bind('input', function() {
        setTimeout(function(){
            checkPasswordMatch();
        }, 100);
    });
    var validateReset = true;
    $("#resetSubmit").click(function(){
        validateReset = true;
        resetEmailPhone();
        resetName();
        PasswordNewCheckLength();
        PasswordNewCheckLength();
        checkPasswordMatch();
        if(validateReset){
            console.log("call reset api")
        }
    });
    function PasswordNewCheckLength(){
        var passwordLength = $("#resetPassword").val();
        if(passwordLength == ""){
            $('#resetPasswordError').html('Please enter password.').show();
            validateReset = false;
        }else if(passwordLength.length < 6){
            $('#resetPasswordError').html('You have to enter at least 6 characters.').show();
            validateReset = false;
        }else {
            $('#resetPasswordError').html('').hide();
        }
    }
    function checkPasswordMatch() {
        $("#resetConfirmPasswordError").html("");
        PasswordNewCheckLength();
        var confirm_password = $('#resetConfirmPassword').val();
        var password = $("#resetPassword").val();
        if(confirm_password == ""){
            $("#resetConfirmPasswordError").html("Please enter confirm password.");
            validateReset = false;
        }else if (password != confirm_password) {
            $("#resetConfirmPasswordError").html("Passwords does not match!");
            validateReset = false;
        }
        else {
            $("#resetConfirmPasswordError").html("");
        }
    }
    function resetName(){
        var resetName = $('#resetName').val();
        if(resetName.length < 1){
            $("#resetNameError").show();
            document.getElementById("resetNameError").innerHTML = "Please enter your name.";
            validateReset = false;
        } else {
            $("#resetNameError").hide();
        }
    }
    function resetEmailPhone(){
        var phone_emailval = $('#resetEmailPhone').val();
        var intRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if(intRegex.test(phone_emailval)){
            if ((phone_emailval.length < 10) || (!intRegex.test(phone_emailval))) {
                $("#resetEmailPhoneError").show();
                document.getElementById("resetEmailPhoneError").innerHTML = "Please enter a valid mobile number.";
                validateReset = false;
            } else {
                $("#resetEmailPhoneError").hide();
            }
        }else if(phone_emailval.length < 1){
            var eml = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
            if (eml.test(phone_emailval) == false) {
                $("#resetEmailPhoneError").show();
                document.getElementById("resetEmailPhoneError").innerHTML = "Please enter an email address or mobile number.";
                validateReset = false;
            } else {
                $("#resetEmailPhoneError").hide();
            }
        }else {
            var eml = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
            if (eml.test(phone_emailval) == false) {
                $("#resetEmailPhoneError").show();
                document.getElementById("resetEmailPhoneError").innerHTML = "Please enter valid email address.";
                validateReset = false;
            } else {
                $("#resetEmailPhoneError").hide();
            }
        }
    }
    $('#submitLoginWithEP').click(function() {
        var phone_emailval = $('#emailPhone').val();
        var password = $('#password').val();
        var intRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if (intRegex.test(phone_emailval)) {
            if ((phone_emailval.length < 10) || (!intRegex.test(phone_emailval))) {
                $("#emailPhoneError").show();
                document.getElementById("emailPhoneError").innerHTML = "Please enter a valid mobile number.";
                passwordFc(password);
            } else {
                $("#emailPhoneError").hide();
                passwordwithFc('mobile', phone_emailval, password);
            }
        } else if (phone_emailval.length < 1) {
            var eml = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
            if (eml.test(phone_emailval) == false) {
                $("#emailPhoneError").show();
                document.getElementById("emailPhoneError").innerHTML = "Please enter an email address or mobile number.";
                passwordFc(password);
            } else {
                $("#emailPhoneError").hide();
                // passwordwithFc(phone_emailval, password);
            }
        } else {
            var eml = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
            if (eml.test(phone_emailval) == false) {
                $("#emailPhoneError").show();
                document.getElementById("emailPhoneError").innerHTML = "Please enter valid email address.";
                passwordFc(password);
            } else {
                $("#emailPhoneError").hide();
                passwordwithFc('email', phone_emailval, password);
            }
        }
    });
    function passwordwithFc(Type, Login, password) {
        if (password.length < 1) {
            $("#passwordError").show();
            document.getElementById("passwordError").innerHTML = "Please enter password.";
        } else {
            $("#passwordError").hide();
            validateLogin(Type, Login,password);
        }
    }
    function passwordFc(password) {
        if (password.length < 1) {
            $("#passwordError").show();
            document.getElementById("passwordError").innerHTML = "Please enter password.";
        } else {
            $("#passwordError").hide();
        }
    }
    function validateLogin(Type, Login, Password) {
        // Login with password API
        $("#submitLoginWithEP").hide();
        $("#show-login-loading").show();
        var Database = $('#field-db').val()
        var params = { 'db': Database, 'login': Login, 'password': Password, 'type': Type || 'email' ,
        };
        ajax.jsonRpc("/bs/user/authenticate", 'call', params).then(function (result) {
            $("#submitLoginWithEP").show();
            $("#show-login-loading").hide();
             $('#error_login').hide();
            if (result['uid'] != false){
                if (result['error']){
                    $('#error_login').html(result['error']).show();
                }
                else{
                    $('#error_login').hide();
                    if(document.referrer){
                        window.location = document.referrer;
                    }
                    else if( sessionStorage['RedirectingURL']){
                        window.location = sessionStorage['RedirectingURL']
                        sessionStorage.removeItem('RedirectingURL');
                    }
                    else{
                        window.location = '/';
                    }
                    //$('#error_login').hide(); window.location = result['redirect_url'] || '/';
                }
            }
            else{
                $('#error_login').html(result['error']).show();
            }
        });
    }
//    //$(".loginOTP, .loginOTPMain").hide();
    $(".loginEP").click(function() {
        $(".loginOTP, .loginOTPMain").show();
        $(".loginEP, .loginEPMain").hide();
    });
    $(".loginOTP").click(function() {
        $(".loginEP, .loginEPMain").show();
        $(".loginOTP, .loginOTPMain").hide();
    });
    // ############################################## LOGIN ###########################################

	$(".bs-track-shipment-btn").click(function(){
		var progressHtml = $(this).parents('.mt-3').find('.bs-track-shipment-progressbar').html();
		$('.track-shipment-progress-dialog').html(progressHtml);
	});
});
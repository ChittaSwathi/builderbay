odoo.define('builderbay.bs_generic', function(require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var rpc = require("web.rpc");

    $(function(){
        var dtToday = new Date();
        var month = dtToday.getMonth() + 1;
        var day = dtToday.getDate();
        var year = dtToday.getFullYear();
        if(month < 10) month = '0' + month.toString();
        if(day < 10) day = '0' + day.toString();
        var minDate= year + '-' + month + '-' + day;
        $('#requested_del_date').attr('min', minDate);
        $('#order_st_date').attr('max', minDate);
        $('#odr_end_date').attr('max', minDate);

        // start date end date validation
//        var start = document.getElementById('order_st_date');
//        var end = document.getElementById('odr_end_date');
//        start.addEventListener('change', function() {
//            if (start.value){
//                end.min = start.value;
//            }
//            if(end.value){
//                var dateOne = new Date(start.value);
//                var dateTwo = new Date(end.value);
//                if (dateOne <= dateTwo) {
//                }else {
//                    end.value = '';
//                }
//            }
//        }, false);
//        end.addEventLiseter('change', function() {
//            if (end.value)
//                start.max = end.value;
//        }, false);
    });

    var start = document.getElementById('order_st_date');
    var end = document.getElementById('odr_end_date');
    function showEnd() {
      if (end.value){
        start.max = end.value;
      }
    }
    function showStart(){
        if (start.value){
            end.min = start.value;
        }
        if(end.value){
            var dateOne = new Date(start.value);
            var dateTwo = new Date(end.value);
            if (dateOne <= dateTwo) {
            }else {
                end.value = '';
            }
        }
    }
    if(end != null){
        end.addEventListener('change', showEnd, false);
    }
    if(start != null){
        start.addEventListener('change', showStart, false);
    }
    // scroll bar fixed while moving scrool

    var el1 = document.querySelector('.target1');
    var el2 = document.querySelector('.target2');
    if(el1 != null){
        var elTop = el1.getBoundingClientRect().top - document.body.getBoundingClientRect().top;
        document.addEventListener('scroll', function (event) {
        const ela = document.querySelector('#wrapwrap');
        if (ela.scrollTop > elTop){
            el1.style.position = 'fixed';
            el1.style.top = '175px';
            el2.style.position = 'fixed';
            el2.style.top = '175px';
            el2.style.right = '32px';
        }
        else
        {
            el1.style.position = 'relative';
            el1.style.top = 'auto';
            el2.style.position = 'relative';
            el2.style.top = 'auto';
            el2.style.right = '0px';
        }
    }, true);
    }

      $('.border-for-all a').hover(
           function(){
                $(this).parent('.border-for-all').addClass('hoverClassShadow');
            },
           function(){
                $(this).parent('.border-for-all').removeClass('hoverClassShadow');
            }
        )

    //Pincode servicability starts
    $(".pincode-serv-container #pincode-serv-value").change(function() {
        $('.pincode-serv-container #pincode-serv-error').html('');
    });
    $('.pincode-serv-container #pincode-serv-check').click(function(e){
        $('.pincode-serv-container #pincode-serv-error').html('').removeClass('text-danger').removeClass('text-success');
        var Pincode = $('.pincode-serv-container #pincode-serv-value').val()
        if (!Pincode){
            $('.pincode-serv-container #pincode-serv-error').html('Please enter pincode').addClass('text-danger')
        }
        else if (Pincode.length < 6){
            $('.pincode-serv-container #pincode-serv-error').html('Please enter a valid pincode').addClass('text-danger')
        }
        else{
            ajax.jsonRpc('/pincode/service',"call", {'pincode': Pincode}).then(function(res){
                $('.pincode-serv-container #pincode-serv-error').html(res[0]).addClass(res[1]);
                if(res[1] == "text-danger"){
                    document.getElementById("clickElement").click();
                }
            })
        }
    })
    //Pincode servicability ends


    //Header - shipping address dropdown -- starts

    $("#address-set").click(function(){
        $(".address-bar-dropdwon").slideToggle();
    });
    $(".address-bar-dropdwon p").click(function(){
        var thisValue = $(this).html();
        var PartnerID = parseInt($("span.addressText").attr('partner-id'))
        var valueText = '<span partner-id="' +PartnerID + '" id="'+ $(this).attr('id')
        + '" class="addressText">' + thisValue + '</span>'
        $("span.addressText").replaceWith(valueText);
        ajax.jsonRpc('/change/address/shipping',"call", {'partner_id': PartnerID,
         'default_shipping_id':parseInt($(this).attr('id'))}).then(function(){location.reload(true)});
    })

    //Header - shipping address dropdown -- ends

//    function readURL(input, EleID) {
//        if (input.files && input.files[0]) {
//            var reader = new FileReader();
//            reader.onload = function(e) {
//                $('#'+EleID).css('background-image', 'url('+e.target.result +')');
//                $('#'+EleID).hide();
//                $('#'+EleID).fadeIn(650);
//            }
//            reader.readAsDataURL(input.files[0]);
//        }
//    }
//    $("#enquiry_attachment").change(function() {
//        readURL(this, 'enq-attach-preview');
//    });
//    $("#delivery_attachment").change(function() {
//        readURL(this, 'del-attach-preview');
//    });

    /* Megamenu - hover dynamic view - STARTS
    $(".megadropdown-toggle a").hover(function(){
        console.log($(this).attr('id'), $(this).attr('parent-id'));
        $('#MegamenuChildCateg' + $(this).attr('id')).show();
        $('#MegamenuBrands' + $(this).attr('parent-id')).hide();

         $('#childCategBrand' + $(this).attr('id')).show();
        $('#childParentCategBrand' + $(this).attr('parent-id')).hide();

        $('#childCategVendor' + $(this).attr('id')).show();
        $('#childParentCategVendor' + $(this).attr('parent-id')).hide();
      }, function(){
      $('#MegamenuChildCateg' + $(this).attr('id')).hide()
      $('#MegamenuBrands' + $(this).attr('parent-id')).show();

       $('#childCategBrand' + $(this).attr('id')).show();
        $('#childParentCategBrand' + $(this).attr('parent-id')).hide();

      $('#childCategVendor' + $(this).attr('id')).show();
        $('#childParentCategVendor' + $(this).attr('parent-id')).hide();
    });
     Megamenu - hover dynamic view - ENDS */


    /* /my/home & Internal Pages JS starts */
    $(".bs-account .nav-tabs li a").click(function (){
        $(".nav-tabs li").removeClass("active"); $(this).parent().addClass("active");
    });
    $('.bs-account .collapse').on('shown.bs.collapse', function () {
        $(this).parent().addClass('active');
    });
    $('.bs-account .collapse').on('hidden.bs.collapse', function () {
        $(this).parent().removeClass('active');
    });

    /* BS enquiry multi select starts */
    var onSelector = {
        get: function (selector) {
            var ele = document.querySelectorAll(selector);
            for (var i = 0; i < ele.length; i++) {
                this.init(ele[i]);
            }
            return ele;
        },
        template: function (html) {
            var template = document.createElement('div');
            template.innerHTML = html.trim();
            return this.init(template.childNodes[0]);
        },
        init: function (ele) {
            ele.on = function (event, func) {
                this.addEventListener(event, func);
            }
            return ele;
        }
    };
    function drop (info) {
        var o = {
            options: info.options,
            selected: info.selected || [],
            preselected: info.preselected || [],
            open: false,
            html: {
                select: onSelector.get(info.selector)[0],
                options: onSelector.get(info.selector + ' option'),
                parent: undefined,
            },
            init: function () {
                if (typeof(onSelector.get(info.selector)[0]) !== 'undefined'){
                    this.html.parent = onSelector.get(info.selector)[0].parentNode
                    this.html.drop = onSelector.template('<div class="drop"></div>')
                    this.html.dropDisplay = onSelector.template('<div class="drop-display" id="display-'+$(onSelector.get(info.selector)[0]).attr('id') +'">Display</div>')
                    this.html.dropOptions = onSelector.template('<div class="drop-options">Options</div>')
                    this.html.dropScreen = onSelector.template('<div class="drop-screen"></div>')
                    this.html.parent.insertBefore(this.html.drop, this.html.select)
                    this.html.drop.appendChild(this.html.dropDisplay)
                    this.html.drop.appendChild(this.html.dropOptions)
                    this.html.drop.appendChild(this.html.dropScreen)
                    this.html.drop.appendChild(this.html.select);
                    var that = this;
                    this.html.dropDisplay.on('click', function () {
                        that.toggle()
                    });
                    this.html.dropScreen.on('click', function () {
                        that.toggle()
                    });
                    this.load()
                    this.preselect()
                    this.render();
                }
            },
            toggle: function () {
                this.html.drop.classList.toggle('open');
            },
            addOption: function (e, element) {
                var index = Number(element.dataset.index);
                this.clearStates()
                this.selected.push({
                    index: Number(index),
                    state: 'add',
                    removed: false
                })
                this.options[index].state = 'remove';
                this.render()
            },
            removeOption: function (e, element) {
                e.stopPropagation();
                this.clearStates()
                var index = Number(element.dataset.index);
                this.selected.forEach(function (select) {
                    if (select.index == index && !select.removed) {
                        select.removed = true
                        select.state = 'remove'
                    }
                })
                this.options[index].state = 'add'
                this.render();
            },
            load: function () {
                this.options = [];
                for (var i = 0; i < this.html.options.length; i++) {
                    var option = this.html.options[i]
                    this.options[i] = {
                        html: option.innerHTML,
                        value: option.value,
                        selected: option.selected,
                        state: '',
                        id : $(option).attr("id"),
                    }
                }
            },
            preselect: function () {
                var that = this;
                this.selected = [];
                this.preselected.forEach(function (pre) {
                    that.selected.push({
                        index: pre,
                        state: 'add',
                        removed: false
                    })
                    that.options[pre].state = 'remove';
                })
            },
            render: function () {
                this.renderDrop()
                this.renderOptions()
            },
            renderDrop: function () {
                var that = this;
                var parentHTML = onSelector.template('<div></div>')
                this.selected.forEach(function (select, index) {
                    var option = that.options[select.index];
                    var childHTML = onSelector.template('<span class="item ' + select.state  + '" id="'+ option.id +  '">' + option.html + '</span>')
                    var childCloseHTML = onSelector.template('<i class="btnclose" data-index="' + select.index + '"></i></span>')
                    childCloseHTML.on('click', function (e) {
                        that.removeOption(e, this)
                    })
                    childHTML.appendChild(childCloseHTML)
                    parentHTML.appendChild(childHTML)
                })
                this.html.dropDisplay.innerHTML = '';
                this.html.dropDisplay.appendChild(parentHTML)
            },
            renderOptions: function () {
                var that = this;
                var parentHTML = onSelector.template('<div></div>')
                this.options.forEach(function (option, index) {
                    var childHTML = onSelector.template('<a data-index="' + index + '" class="' + option.state + '" id="'+ option.id + '" >' + option.html + '</a>')
                    childHTML.on('click', function (e) {
                        that.addOption(e, this)
                    })
                    parentHTML.appendChild(childHTML)
                })
                this.html.dropOptions.innerHTML = '';
                this.html.dropOptions.appendChild(parentHTML)
            },
            clearStates: function () {
                var that = this;
                this.selected.forEach(function (select, index) {
                    select.state = that.changeState(select.state)
                })
                this.options.forEach(function (option) {
                    option.state = that.changeState(option.state)
                })
            },
            changeState: function (state) {
                switch (state) {
                    case 'remove':
                        return 'hide'
                    case 'hide':
                        return 'hide'
                    default:
                        return ''
                }
            },
            isSelected: function (index) {
                var check = false
                this.selected.forEach(function (select) {
                    if (select.index == index && select.removed == false) check = true
                })
                return check
            }
        };
        o.init();
        return o;
    }
    drop({
        selector: '.leave-enquiry #EnquiryLocation',
    //	preselected: [0,3]
      });
    drop({
    selector: '.leave-enquiry #EnqBrands',
    //	preselected: [0, 2]
    });
    drop({
    selector: '.leave-enquiry #categories',
    //	preselected: [0,3]
    });
    drop({
        selector: '.leave-enquiry #subcategories',
    //	preselected: [0, 2]
      });
    /* BS enquiry multi select ends */






    /* Portal - BS enquiry starts */


    $('.leave-enquiry .drop-display#display-EnquiryLocation').bind("DOMSubtreeModified",function(){
        if ($('#display-EnquiryLocation span:not(.remove,.hide)').length > 0){$('#states-error').hide()}
        else{$('#states-error').show()}
    })
    $('.leave-enquiry .drop-display#display-categories').bind("DOMSubtreeModified",function(){
        if ($('#display-categories span:not(.remove,.hide)').length > 0){$('#categories-error').hide()}
        else{$('#categories-error').show()}
    })
    $('.leave-enquiry .drop-display#display-subcategories').bind("DOMSubtreeModified",function(){
        if ($('#display-subcategories span:not(.remove,.hide)').length > 0){$('#subcategories-error').hide()}
        else{$('#subcategories-error').show()}
    })
    $('.leave-enquiry .drop-display#display-EnqBrands').bind("DOMSubtreeModified",function(){
        if ($('#display-EnqBrands span:not(.remove,.hide)').length > 0){$('#brands-error').hide()}
        else{$('#brands-error').show()}
    })

    var States = [], categories = [], subcategories = [], EnqBrands = []
    $( ".bs-enquiry-submit" ).click(function( event ) {
        $('.leave-enquiry .drop-display#display-EnquiryLocation span').each(function(){
            States.push($(this).attr('id'))
        })
        $('.leave-enquiry .drop-display#display-categories span').each(function(){
            categories.push($(this).attr('id'))
        })
        $('.leave-enquiry .drop-display#display-subcategories span').each(function(){
            subcategories.push($(this).attr('id'))
        })
        $('.leave-enquiry .drop-display#display-EnqBrands span').each(function(){
            EnqBrands.push($(this).attr('id'))
        })
        if($('#materialQN').val() == ""){
            $("#materialQN-error").html('Please enter material quantity.').show();
        }else {
            $("#materialQN-error").html('').hide();
        }
        if (States.length == 0 || categories.length == 0 || subcategories.length == 0 || EnqBrands.length == 0){
            if (States.length == 0){$('span#states-error').html('Please select location(s).')}
            else{$('span#states-error').html('')}

            if (categories.length == 0){$('span#categories-error').html('Please select type(s).')}
            else{$('span#categories-error').html('')}

            if (subcategories.length == 0){$('span#subcategories-error').html('Please select subtype(s).')}
            else{$('span#subcategories-error').html('')}

            if (EnqBrands.length == 0){$('span#brands-error').html('Please select brand(s).')}
            else{$('span#brands-error').html('')}
        }
        else{
            $("#materialQN-error").html('').hide();
            $('span#states-error').html('')
            $('span#categories-error').html('')
            $('span#subcategories-error').html('')
            $('span#brands-error').html('')
            ajax.jsonRpc("/create/enquiry", 'call',{
                'type': 'PriceEnquiry',
                'location_ids': States,
                'quantity': parseInt($('.leave-enquiry #materialQN').val()),
                'brand_ids':EnqBrands,
                'ecomm_subcateg_ids':subcategories,
                'ecomm_category_ids':categories,
                'uom_id': parseInt($('.leave-enquiry #uom option:selected').attr('id')),
                'material_description': $.trim($(".leave-enquiry #description").val()),
                'partner_id': parseInt($('#partner-id').val()),
                })
                .then(function (res) {
                    if (res){
                        swal("Success!", "Enquiry has been successfully submitted.", "success").then((ok) => {
                          if (ok) {window.location = '/my/enquiries'}
                        });
                    }
                    else{
                        swal("OOPS!", `Please recheck values.`, "error");
                    }
            })
        }
    });
    /* Portal - BS enquiry ends */

   /* Contact us page --- starts */
   $('.input-name-cont').keyup(function() {
        if($(".input-name-cont").val() == ""){
            $('#error_name_cont').html('Please enter your name.').show();
        }else{
            $("#error_name_cont").html("").hide();
        }
   });
   $('.input-email-cont').keyup(function() {
        var EmailRegex = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
        if($(".input-email-cont").val() == ""){
            $('#error_email_cont').html('Please enter your email.').show();
        }else if(EmailRegex.test($(".input-email-cont").val()) == false){
            $("#error_email_cont").html("Please enter valid email address.").show();
        }else{
            $("#error_email_cont").html("").hide();
        }
   });
   $('.input-phone-cont').keyup(function() {
        var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if($('.input-phone-cont').val() == ""){
            $('#error_phone_cont').html('Please enter your mobile number.').show();
        }else if(!MobileRegex.test($('.input-phone-cont').val()) || ($('.input-phone-cont').val().length < 10)){
            $("#error_phone_cont").html("Please enter valid mobile number.").show();
        }else{
            $("#error_phone_cont").html("").hide();
        }
   });
   $('#bs-contact-us').click(function(){
        var valid = true

        var EmailRegex = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
        if($(".input-name-cont").val() == ""){
            $('#error_name_cont').html('Please enter your name.').show();
            valid = false;
        }else{
            $("#error_name_cont").html("").hide();
        }

        if($(".input-email-cont").val() == ""){
            $('#error_email_cont').html('Please enter your email.').show();
            valid = false;
        }else if(EmailRegex.test($(".input-email-cont").val()) == false){
            valid = false;
            $("#error_email_cont").html("Please enter valid email address.").show();
        }else{
            $("#error_email_cont").html("").hide();
        }

        var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
        if($('.input-phone-cont').val() == ""){
            $('#error_phone_cont').html('Please enter your mobile number.').show();
            valid = false;
        }else if(!MobileRegex.test($('.input-phone-cont').val()) || ($('.input-phone-cont').val().length < 10)){
            $("#error_phone_cont").html("Please enter valid mobile number.").show();
            valid = false;
        }else{
            $("#error_phone_cont").html("").hide();
        }

        var FinalVals = {'contact_name': $('#your-name').val(),
                    'phone': $('#phone-number').val(),
                    'email_from': $('#email').val(),
                    'partner_name': $('#company').val(),
                    'name': $('#subject').val(),
                    'description': $('#question').val()
                    }
        if (valid){
            ajax.jsonRpc('/bs/contactus',"call", FinalVals).then(function(result){
                if (result != false){
                    swal("Success!", "Your contact has been sent successfully. We will get back to you shortly.", "success").then((ok) => {
                      if (ok) {location.reload();}
                    });
                }
                else{
                    swal("OOPS!", `Something went wrong.`, "error");
                }
            });
        }
    });
    /* Contact us page --- ends */

});
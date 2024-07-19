// ####################### LEFT SECTION STARTS ##################################
// ---------------------- SIBLING CATEGORIES STARTS ------------------------------

$("#steelTmtBarsUL li").hide();
$('.sibling-categ').click(function() {
    var URL = window.location.href
    if($(this).prop("checked") == true){
        if (URL.indexOf('?search=') != -1){ window.location = URL + '&attribCat=' + $(this).attr('id')}
        else{ window.location = '/shop?search=&attribCat=' + $(this).attr('id')}
    }
    else{
        var count = (URL.match('&attribCat=') || []).length;
        if (count > 1){
            var newURL = URL.replace('&attribCat=' + $(this).attr('id'), "");
            window.location = newURL
        }
        else{
            window.location = $(this).attr('parent-url')
        }
    }
//  if($(this).prop("checked") == true){
//    window.location = '/shop?search=&attribCat=' + $(this).attr('id')
//  }
//  else{
//    window.location = '/shop'
//  }
});
function searchTMTBars(event){
    $("#plus5More").hide();
    if(!event){
        setTimeout(function(){
            var $lis = $("#steelTmtBarsUL li").hide();
            $lis.slice(0, plus5MoreCount).show();
            var steel_size_li = $("#steelTmtBarsUL").find("li").length;
            if(plus5MoreCount == steel_size_li){
                $("#plus5More").hide();
            }else{
                $("#plus5More").show();
            }
        });
    }
    $("#steelTmtBarsUL li").show();
    var input, filter, ul, li, label, i, txtValue;;
    input = document.getElementById("searchSteelTMTBar");
    filter = input.value.toUpperCase();
    ul = document.getElementById("steelTmtBarsUL");
    li = ul.getElementsByTagName("li");
    for (i = 0; i < li.length; i++) {
        label = li[i].getElementsByTagName("label")[0];
        txtValue = label.textContent || label.innerText;

        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
    }
}
var steel_size_li = $("#steelTmtBarsUL").find("li").length;
plus5MoreCount = 7;
$('#steelTmtBarsUL li:lt('+plus5MoreCount+')').show();
$('#plus5More').click(function () {
    plus5MoreCount= (plus5MoreCount+5 <= steel_size_li) ? plus5MoreCount+5 : steel_size_li;
    $('#steelTmtBarsUL li:lt('+plus5MoreCount+')').show();
    if(plus5MoreCount >= steel_size_li){
        setTimeout(function(){
            $("#plus5More").hide();
        });
    }
});
if(plus5MoreCount >= steel_size_li){
    setTimeout(function(){
        $("#plus5More").hide();
    });
}
$("#sortTMTasc").hide();
$("#steelTMTHeadeinng").click(function(){
    $(".TMTBarMainSlide").slideToggle();
    $(".TMTascdesc").toggle();
});
//---------------------- SIBLING CATEGORIES ENDS ------------------------------

//---------------------- CHILD CATEGORIES STARTS ------------------------------
$("#steelStructuralBarsUL li").hide();
$('.child-categ').click(function() {
    var URL = window.location.href
    if($(this).prop("checked") == true){
        if (URL.indexOf('?search=') != -1){ window.location = URL + '&attribCat=' + $(this).attr('id')}
        else{ window.location = '/shop?search=&attribCat=' + $(this).attr('id')}
    }
    else{
        var newURL = URL.replace('&attribCat=' + $(this).attr('id'), "");
        window.location = newURL
    }
});
function searchStructuralBars(event){
    if(!event){
        setTimeout(function(){
            var $lis = $("#steelStructuralBarsUL li").hide();
            $lis.slice(0, plus10MoreCount).show();
        });
    }
    $("#steelStructuralBarsUL li").show();
    var input, filter, ul, li, label, i, txtValue;;
    input = document.getElementById("searchSteelStructuralBar");
    filter = input.value.toUpperCase();
    ul = document.getElementById("steelStructuralBarsUL");
    li = ul.getElementsByTagName("li");
    for (i = 0; i < li.length; i++) {
        label = li[i].getElementsByTagName("label")[0];
        txtValue = label.textContent || label.innerText;

        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
    }
}
var structural_size_li = $("#steelStructuralBarsUL").find("li").length;
plus10MoreCount=7;
$('#steelStructuralBarsUL li:lt('+plus10MoreCount+')').show();
$('#plus10More').click(function () {
    plus10MoreCount= (plus10MoreCount+5 <= structural_size_li) ? plus10MoreCount+5 : structural_size_li;
    $('#steelStructuralBarsUL li:lt('+plus10MoreCount+')').show();
    if(plus10MoreCount >= structural_size_li){
        setTimeout(function(){
            $("#plus10More").hide();
        });
    }
});
if(plus10MoreCount >= structural_size_li){
    setTimeout(function(){
        $("#plus10More").hide();
    });
}
$("#sortStructuralasc").hide();
//$(".StructuralBarMainSlide").hide();
$("#steelStructuralHeadeinng").click(function(){
    $(".StructuralBarMainSlide").slideToggle();
    $(".Structuralascdesc").toggle();
});
//---------------------- CHILD CATEGORIES ENDS ------------------------------


// ---------------------- ALL BRANDS STARTS ----------------------------
$("#allBrandsUL li").hide();
$('.filter-all-brand').click(function() {
    var URL = window.location.href
    if($(this).prop("checked") == true){
        if (URL.indexOf('?search=') != -1){ window.location = URL + '&attrib=' + $(this).attr('attribute-id') + '-' + $(this).attr('id')}
        else{ window.location = '/shop?search=&attrib=' + $(this).attr('attribute-id') + '-' + $(this).attr('id')}
    }
    else{
        var newURL = URL.replace('&attrib=' + $(this).attr('attribute-id') + '-' + $(this).attr('id'), "");
        window.location = newURL
    }
});
function searchAllBars(event){
    if(!event){
        setTimeout(function(){
            var $lis = $("#allBrandsUL li").hide();
            $lis.slice(0, plusPrimaryMoreCount).show();
        });
    }
    $("#allBrandsUL li").show();
    var input, filter, ul, li, label, i, txtValue;;
    input = document.getElementById("searchAllBrands");
    filter = input.value.toUpperCase();
    ul = document.getElementById("allBrandsUL");
    li = ul.getElementsByTagName("li");
    for (i = 0; i < li.length; i++) {
        label = li[i].getElementsByTagName("label")[0];
        txtValue = label.textContent || label.innerText;

        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
    }
}
var primary_size_li = $("#allBrandsUL").find("li").length;
plusPrimaryMoreCount=6;
$('#allBrandsUL li:lt('+plusPrimaryMoreCount+')').show();
$('#viewAllBrandsMore').click(function () {
    plusPrimaryMoreCount = primary_size_li;
    $('#allBrandsUL li').show();
    $("#viewAllBrandsMore").hide();
});
if(plusPrimaryMoreCount >= primary_size_li){
    setTimeout(function(){
        $("#viewAllBrandsMore").hide();
    });
}
$("#sortAllBrandsasc").hide();
$("#steelBrandsHeadeinng").click(function(){
    $(".AllBrandsMainSlide").slideToggle();
    $(".AllBrandsascdesc").toggle();
});
// ---------------------- ALL BRANDS ENDS ------------------------------

// ---------------------- SAFETY BRANDS STARTS DYNAMIC -------------------------
$(".BSAttrVals li").hide();
$(".bs-bar-under").each(function(){
    var primary_size_li = $(this).find(".BSAttrVals li").length;
    plusPrimaryMoreCount=6;
    $(this).find('.BSAttrVals li:lt('+plusPrimaryMoreCount+')').show();
    if(plusPrimaryMoreCount >= primary_size_li){
        $(this).find(".bsViewMoreBtn").hide();
    }
});
$( '.primaryBarMain' ).on( 'click', '.bsViewMoreBtn', function( event ) {
    event.preventDefault();
    var parentId = $(this).closest('div.bs-bar-under').attr('id');
    $('#'+parentId+' '+ '.BSAttrVals li').show();
    $(this).hide();
});
$(".bsdsc").hide();
$(".BSAttrValHeading").click(function(){
    var parentId = $(this).closest('div.bs-bar-under').attr('id');
    $('#'+parentId+' '+".AllBrandsMainSlide").slideToggle();
    $('#'+parentId+' '+".AllBrandsascdesc").toggle();
});
$('.BSsearchBar').keyup(function(event){
    var parentId = $(this).closest('div.bs-bar-under').attr('id');
    var currentID = $(this).attr('id');
    var bSUlDiv = $('#'+parentId+' '+ '.BSAttrVals').attr('id');

    if(!event.target.value){
        setTimeout(function(){
            var $lis = $('#'+parentId+' '+ '.BSAttrVals li').hide();
            $lis.slice(0, 6).show();
        });
    }
    $('#'+parentId+' '+ '.BSAttrVals li').show();
    var input, filter, ul, li, label, i, txtValue;;
    input = document.getElementById(currentID);
    filter = input.value.toUpperCase();
    ul = document.getElementById(bSUlDiv);
    li = ul.getElementsByTagName("li");
    for (i = 0; i < li.length; i++) {
        label = li[i].getElementsByTagName("label")[0];
        txtValue = label.textContent || label.innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
    }
});

// ---------------------- SAFETY BRANDS STARTS ENDS -------------------------

/*
// ---------------------- PRIMARY BRANDS STARTS ----------------------------
$("#steelPrimaryBarsUL li").hide();
$('.filter-primary-brand').click(function() {
//  $('.filter-primary-brand').not(this).prop('checked', false);
  if($(this).prop("checked") == true){
    window.location = '/shop?search=&attrib='+ $(this).attr('attribute-id') + '-' + $(this).attr('id')
  }
  else{
    window.location = '/shop'
  }
});
function searchPrimaryBars(event){
    if(!event){
        setTimeout(function(){
            var $lis = $("#steelPrimaryBarsUL li").hide();
            $lis.slice(0, plusPrimaryMoreCount).show();
        });
    }
    $("#steelPrimaryBarsUL li").show();
    var input, filter, ul, li, label, i, txtValue;;
    input = document.getElementById("searchSteelPrimaryBar");
    filter = input.value.toUpperCase();
    ul = document.getElementById("steelPrimaryBarsUL");
    li = ul.getElementsByTagName("li");
    for (i = 0; i < li.length; i++) {
        label = li[i].getElementsByTagName("label")[0];
        txtValue = label.textContent || label.innerText;

        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
    }
}
var primary_size_li = $("#steelPrimaryBarsUL").find("li").length;
plusPrimaryMoreCount=6;
$('#steelPrimaryBarsUL li:lt('+plusPrimaryMoreCount+')').show();
$('#viewPrimaryMore').click(function () {
    plusPrimaryMoreCount = primary_size_li;
    $('#steelPrimaryBarsUL li').show();
    $("#viewPrimaryMore").hide();
});
if(plusPrimaryMoreCount >= primary_size_li){
    setTimeout(function(){
        $("#viewPrimaryMore").hide();
    });
}
$("#sortBrandsasc").hide();
$("#steelBrandsHeadeinng").click(function(){
    $(".primaryBarMainSlide").slideToggle();
    $(".Brandsascdesc").toggle();
});
// ---------------------- PRIMARY BRANDS ENDS ------------------------------

// ---------------------- SECONDARY BRANDS STARTS --------------------------
$("#steelSecondaryBarsUL li").hide();
$('.filter-secondary-brand').click(function() {
//  $('.filter-secondary-brand').not(this).prop('checked', false);
  if($(this).prop("checked") == true){
    window.location = '/shop?search=&attrib='+ $(this).attr('attribute-id') + '-' + $(this).attr('id')
  }
  else{
    window.location = '/shop'
  }
});
function searchSecondaryBars(event){
    if(!event){
        setTimeout(function(){
            var $lis = $("#steelSecondaryBarsUL li").hide();
            $lis.slice(0, plusSecondaryMoreCount).show();
        });
    }
    $("#steelSecondaryBarsUL li").show();
    var input, filter, ul, li, label, i, txtValue;;
    input = document.getElementById("searchSteelSecondaryBar");
    filter = input.value.toUpperCase();
    ul = document.getElementById("steelSecondaryBarsUL");
    li = ul.getElementsByTagName("li");
    for (i = 0; i < li.length; i++) {
        label = li[i].getElementsByTagName("label")[0];
        txtValue = label.textContent || label.innerText;

        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
    }
}
var secondary_size_li = $("#steelSecondaryBarsUL").find("li").length;
plusSecondaryMoreCount=6;
$('#steelSecondaryBarsUL li:lt('+plusSecondaryMoreCount+')').show();
$('#viewSecondaryMore').click(function () {
    plusSecondaryMoreCount = secondary_size_li;
    $('#steelSecondaryBarsUL li').show();
    $("#viewSecondaryMore").hide();
});
if(plusSecondaryMoreCount >= secondary_size_li){
    setTimeout(function(){
        $("#viewSecondaryMore").hide();
    });
}
// ---------------------- SECONDARY BRANDS ENDS ------------------------------

*/
// ####################### LEFT SECTION ENDS ##################################


// start chips category_names
$('.chipsSelect').each(function(index, value) {
	var thisid = `${this.id}`;
	$("#"+thisid+" "+".greadechips").hide();
	var greadeChips_size_li = $("#"+thisid).find(".greadechips").length;
	plusgreadeChipsMoreCount = 6;
	$('#'+thisid+ ' ' +'.greadechips:lt('+plusgreadeChipsMoreCount+')').show();
});
$('.chipsMore').click(function () {
	var thisid = `${this.id}`;
	var slicebtnsID = thisid.slice(8);
    $('#gradeChips'+slicebtnsID+ ' ' +'.greadechips').show();
	$("#"+thisid).hide();
});
// ends chips category_names


// start view more ABOUT THE PRODUCT
var maxLength = 372;
$(".show-more").hide();
$(".show-read-more").each(function(){
	var myStr = $(this).text();
	if($.trim(myStr).length > maxLength){
		var newStr = myStr.substring(0, maxLength);
		var removedStr = myStr.substring(maxLength, $.trim(myStr).length);
		$(this).empty().html(newStr);
		$(this).append(' <a href="javascript:void(0);" class="read-more pointer text-color-blue-1 text-underline font-size-14 font-family-bold">view more</a>');
		$(this).append('<p class="more-text">' + removedStr + '</p>');
	}
});
$(".read-more").click(function(){
	$(this).remove();
	$(".show-more").show();
	$(".show-read-more").hide();
});
// ends view more ABOUT THE PRODUCT

// start product view images and content
$('.carosel-control-right').click(function() {
  $(this).blur();
  $(this).parent().find('.product-image-box').first().insertAfter($(this).parent().find('.product-image-box').last());
});
$('.carosel-control-left').click(function() {
  $(this).blur();
  $(this).parent().find('.product-image-box').last().insertBefore($(this).parent().find('.product-image-box').first());
});
function changeImage(imageURL){
	$(".image-show").css("background-image", "url(" + imageURL + ")");
}
$('.product-image-box img').bind('click', function() {
    $('.product-image-box-img-active').removeClass('product-image-box-img-active')
    $(this).addClass('product-image-box-img-active');
});
var secondary_size_li = $(".slide-left-right").find(".product-image-box").length;
if(secondary_size_li <= 4){
	setTimeout(function(){
		$(".carosel-control-left, .carosel-control-right").hide();
	});
}

$('.product-image-box').click(function(e) {
    $(".image-show img").attr('src', e.target.currentSrc);
});

// ends product view images and content

// Add addquantityBox start
//var num = 0;
//function addquantityBox(titleText){
//	num++;
//    $("#"+titleText).toggleClass('chips-active');
//
//    if($("#"+titleText).hasClass("chips-active")){
//		$("#quantity_parent").append($("#quantity-part1").clone().prop({'id': 'show'+titleText}));
//		$("#show"+titleText).show();
//
//		$("#show"+titleText+" "+ ".plusIcon").attr('id', "plus"+titleText);
//		$("#show"+titleText+" "+ ".lessIcon").attr('id', "less"+titleText);
//
//		$("#show"+titleText+" "+ ".ton-input").attr('id', "tons"+titleText);
//		$("#show"+titleText+" "+ ".rod-input").attr('id', "rods"+titleText);
//		$('.quantity-part-and-quantity-box').each(function(index, value) {
//			var thisid = `${this.id}`;
//			$("#"+thisid+" "+".dynamic-number").text(index);
//		});
//    }else{
//    	var $removeQuantityDiv = $("#show"+titleText);
//        $removeQuantityDiv.remove();
//    }
//}
//var tonInputClick = false;
//var rodInputClick = false;
//function rodsInput(event){
//	window.rodInputClick = true;
//	window.tonInputClick = false;
//}
//function tonsInput(event){
//	window.rodInputClick = false;
//	window.tonInputClick = true;
//}
//function rodsonInput(event, id, inputValue){
//	if(event != ""){
//		var inputRodsId = event.target.id;
//		var slicerodsID = inputRodsId.slice(4);
//		var rodsInputValue = event.target.value;
//		var tonsInputValueChange = rodsInputValue * 4.75 / 1000; // backened value
//		$("#"+"tons"+slicerodsID).val(tonsInputValueChange)
//	}else{
//		var inputRodsId = id;
//		var slicerodsID = inputRodsId.slice(4);
//		var rodsInputValue = inputValue;
//		var tonsInputValueChange = rodsInputValue * 4.75 / 1000; // backened value
//		$("#"+"tons"+slicerodsID).val(tonsInputValueChange)
//	}
//}
//function tonsonInput(event, id, inputValue){
//	if(event != ""){
//		var inputTonssId = event.target.id;
//		var slicetonsID = inputTonssId.slice(4);
//		var tonsInputValue = event.target.value;
//		var rodsInputValueChange = tonsInputValue * 211; // backened value
//		var removedrodsInputValueChangeDecimal = Math.trunc(rodsInputValueChange);
//		$("#"+"rods"+slicetonsID).val(removedrodsInputValueChangeDecimal);
//	}else{
//		var inputTonssId = id;
//		var slicetonsID = inputTonssId.slice(4);
//		var tonsInputValue = inputValue;
//		var rodsInputValueChange = tonsInputValue * 211; // backened value
//		var removedrodsInputValueChangeDecimal = Math.trunc(rodsInputValueChange);
//		$("#"+"rods"+slicetonsID).val(removedrodsInputValueChangeDecimal);
//	}
//}
//function addCalculation(event){
//	if(rodInputClick){
//		var plusid = event.target.id.slice(4);
//		var getParentinput = "show"+plusid;
//		var inputValue = $("#"+getParentinput +" "+ ".rod-input").val();
//		var removedinputValueDecimal = Math.trunc(inputValue);
//		var decimalInputValue = (inputValue + "").split(".")[1];
//		var addInputValueOne = removedinputValueDecimal+1;
//		if(decimalInputValue != undefined){
//			$("#"+getParentinput +" "+ ".rod-input").val(addInputValueOne+"."+decimalInputValue);
//			var rodId = $("#"+getParentinput +" "+ ".rod-input").attr('id');
//			rodsonInput("", rodId, addInputValueOne+"."+decimalInputValue);
//		}else{
//			$("#"+getParentinput +" "+ ".rod-input").val(addInputValueOne);
//			var rodId = $("#"+getParentinput +" "+ ".rod-input").attr('id');
//			rodsonInput("", rodId, addInputValueOne);
//		}
//	}else if(tonInputClick){
//		var plusid = event.target.id.slice(4)
//		var getParentinput = "show"+plusid;
//		var inputValue = $("#"+getParentinput +" "+ ".ton-input").val();
//		var removedinputValueDecimal = Math.trunc(inputValue);
//		var decimalInputValue = (inputValue + "").split(".")[1];
//		var addInputValueOne = removedinputValueDecimal+1;
//		if(decimalInputValue != undefined){
//			$("#"+getParentinput +" "+ ".ton-input").val(addInputValueOne+"."+decimalInputValue)
//			var tonId = $("#"+getParentinput +" "+ ".ton-input").attr('id');
//			tonsonInput("", tonId, addInputValueOne+"."+decimalInputValue);
//		}else{
//			$("#"+getParentinput +" "+ ".ton-input").val(addInputValueOne)
//			var tonId = $("#"+getParentinput +" "+ ".ton-input").attr('id');
//			tonsonInput("", tonId, addInputValueOne);
//		}
//	}else{
//		alert("Please select TON(S) or PIECES / RODS");
//	}
//
//}
//function minusCalculation(event){
//	if(rodInputClick){
//		var lessid = event.target.id.slice(4);
//		var getParentinput = "show"+lessid;
//		var inputValue = $("#"+getParentinput +" "+ ".rod-input").val();
//		if(inputValue != 0){
//			var removedinputValueDecimal = Math.trunc(inputValue);
//			var decimalInputValue = (inputValue + "").split(".")[1];
//			var lessInputValueOne = removedinputValueDecimal-1;
//			if(decimalInputValue != undefined){
//				$("#"+getParentinput +" "+ ".rod-input").val(lessInputValueOne+"."+decimalInputValue)
//				var rodId = $("#"+getParentinput +" "+ ".rod-input").attr('id');
//				rodsonInput("", rodId, lessInputValueOne+"."+decimalInputValue);
//			}else{
//				$("#"+getParentinput +" "+ ".rod-input").val(lessInputValueOne)
//				var rodId = $("#"+getParentinput +" "+ ".rod-input").attr('id');
//				rodsonInput("", rodId, lessInputValueOne);
//			}
//		}
//	}else if(tonInputClick){
//		var lessid = event.target.id.slice(4);
//		var getParentinput = "show"+lessid;
//		var inputValue = $("#"+getParentinput +" "+ ".ton-input").val();
//		var removedinputValueDecimal = Math.trunc(inputValue);
//		if(removedinputValueDecimal != 0){
//			var decimalInputValue = (inputValue + "").split(".")[1];
//		var lessInputValueOne = removedinputValueDecimal-1;
//		if(decimalInputValue != undefined){
//			$("#"+getParentinput +" "+ ".ton-input").val(lessInputValueOne+"."+decimalInputValue)
//				var tonId = $("#"+getParentinput +" "+ ".ton-input").attr('id');
//				tonsonInput("", tonId, lessInputValueOne+"."+decimalInputValue);
//			}else{
//				$("#"+getParentinput +" "+ ".ton-input").val(lessInputValueOne);
//				var tonId = $("#"+getParentinput +" "+ ".ton-input").attr('id');
//				tonsonInput("", tonId, lessInputValueOne);
//			}
//		}
//	}else{
//		alert("Please select TON(S) or PIECES / RODS");
//	}
//}
// Add addquantityBox ends



odoo.define('builderbay.CustomPDP', function (require) {
    "use strict";

    var rpc = require('web.rpc')
    require('web.dom_ready');
    var ajax = require('web.ajax');
    var session = require('web.session');
    $('[data-toggle="tooltip"]').tooltip();

    var EmailRegex = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
    var MobileRegex = /^\d*[0-9-+](|.\d*[0-9-+]|,\d*[0-9-+])?$/;
    var GSTRegex = /^([0][1-9]|[1-2][0-9]|[3][0-7])([a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}[1-9a-zA-Z]{1}[zZ]{1}[0-9a-zA-Z]{1})+$/;
    var PANRegex = /^[A-Z]{3}[ABCFGHLJPT][A-Z][0-9]{4}[A-Z]$/;
    var AllCharsRegex = /^[ A-Za-z]+$/;
    var AllNumericRegex= /^[0-9]+$/;
    var AlphanumericRegex = /^[a-zA-Z0-9]$/;

    //Bulk enquiry - base64
    function encodeImageFileAsURL(cb) {
        return function(){
            var file = this.files[0];
            var reader  = new FileReader();
            reader.onloadend = function () { cb(reader.result); }
            reader.readAsDataURL(file);
        }
    }
    $('#gstin_attachment').change(encodeImageFileAsURL(function(base64Img){
        $('#gstin_attachment_base64').val(base64Img.replace(/^data:.+;base64,/, ''));
    }));
     $('#logo_attachment').change(encodeImageFileAsURL(function(base64Img){
        $('#logo_attachment_base64').val(base64Img.replace(/^data:.+;base64,/, ''));
    }));

    $("#menu-toggle, #filter_icon").click(function(){
        $('.filter-open').attr('style', 'display: none !important');
        $('#wrapwrap').css('height','auto');
        $(".steel-main-content").css("padding-left", "0px");
        $(".steel-main-content").css("padding-right", "0px");
        $(".mobile-filter").show();
        var left = $('.left-bars-selection').offset().left;
        $(".left-bars-selection").css({left:left}).animate({"left":"0px"}, "slow");
    });
    $(".go-left-filter").click(function(){
        $('.filter-open').attr('style', 'display: block !important');
        $('#wrapwrap').css('height','100%');
        var left = $('.left-bars-selection').offset().left;
        $(".left-bars-selection").css({left:left}).animate({"left":"-500px"}, "slow");
        setTimeout(function(){
            $(".mobile-filter").hide();
            $(".steel-main-content").css("padding-left", "10px");
            $(".steel-main-content").css("padding-right", "10px");
        },500);
    });

    // ##################### TOP ATTRIBUTES SELECTION/UNSELECTION STARTS ########################################
    $('.selection-chips').click(function(e) { // controls toggle on selection-chips & qty box display/hide
    		
			var AttributeValueIDs = []
			var AttributeValueNames = []
			var cat_inverted = {}
			var s3 = []
            if ($('.selected-attr'+$(this).attr('attribute-id')+ ' .chips-active').not('.chipsMore').length == 1){
                // stop disabling the only selected chip
                if ($(this).attr('multi-select') == '1'){$(this).not('.chips-active').toggleClass('chips-active');}
                else{
                    $('.selected-attr'+$(this).attr('attribute-id')+ ' .chips-active').toggleClass('chips-active').prop('checked', function(i, v) { return !v; });
                    $(this).toggleClass('chips-active');
                }
            }
            else{ $(this).toggleClass('chips-active');
             }

            // Append selection chip data to specifications
            var AttrStr = ''
            $('.selected-attr'+$(this).attr('attribute-id')+ ' .Attr-val').each(function(){
                if ($(this).hasClass('chips-active')){
                    if (AttrStr != ''){ AttrStr += ', '}
                    AttrStr = AttrStr + $(this)[0].innerText;
                }
            })
            
            $('div#'+ $(this).attr('attribute-id') +'.dynamic-spec').html(AttrStr);

            // Hide / Show Product Qty Box
            $('.selection-chips.chips-active').each(function(){ 
            	AttributeValueIDs.push(parseInt($(this).attr('id')));
            	var attr_id = parseInt($(this).attr('id'));
            	var attr_name = $(this).attr('value-name');
        	    if (cat_inverted[attr_name]) {
        	    	if(!Number.isNaN(attr_id)){
        	    		cat_inverted[attr_name].push($(this)[0].innerText.trim().replace(/\s/g, '_'));
        	    	}
        	        
        	    } else {
        	    	if(!Number.isNaN(attr_id)){
        	    		if (attr_name == 'Brand'){
        	    			cat_inverted[attr_name] = [attr_id];
        	    		}else{
        	    			cat_inverted[attr_name] = [$(this)[0].innerText.trim().replace(/\s/g, '_')];
        	    		}
        	    		
        	    		AttributeValueNames.push(cat_inverted);
        	    	}
        	    }
            })

            var param = '?' + $.map(AttributeValueNames[0], function(v, k) {
            	var tex = v.join();
                return encodeURIComponent(k) + '=' + tex;
            }).join('&');
            const newArray = AttributeValueIDs.filter(function (value) {
                return !Number.isNaN(value);
            });
            window.history.replaceState(null, null, param+'&attribute='+newArray);
            ajax.jsonRpc("/show_variant_list", 'call',{
                'attribute_ids': AttributeValueIDs,
                'product_tmpl_id': parseInt($('#ProdTempID').val()),
            })
            .then(function (res) {
                var Prod2Display = res.displayProd;
				
				const prodImag = document.createElement('img');
		        prodImag.setAttribute('src', res.image);
				$('.image-show').empty();
				$('.image-show').html(prodImag);
                $('.quantity-part-and-quantity-box').each(function(){ // Steel
                    if ($.inArray(parseInt($(this).attr('product-id')), Prod2Display) ==-1){$(this).hide();}
                    else {$(this).show();}
                });
                $('.cement-qty-box tr.variant-row').each(function(){ // Cement
                    if ($.inArray(parseInt($(this).attr('id')), Prod2Display) ==-1){$(this).hide();}
                    else {$(this).show();}
                });
            });
//        }
    });
    // ##################### TOP ATTRIBUTES SELECTION/UNSELECTION ENDS ########################################


    // ##################### +, - ICONS CLICK STARTS ###########################################
    $('.plusIcon').click(function(e){
        var ProdID = $(this).attr('id')
        var CurrentQty = parseFloat($('div#'+ ProdID +' input.active-input').val() || 0.00)
        var NewQty = parseFloat(CurrentQty + 1.00).toFixed(3)
        $('div#'+ ProdID +' input.active-input').each(function(e){
            $(this).attr('value', (NewQty)).val(NewQty).change();
        })
        //UpdateCombinationPrice(ProdID, NewQty);TODO: open later
    });
    $('.lessIcon').click(function(e){
        var ProdID = $(this).attr('id')
        var CurrentQty = parseFloat($('div#'+ ProdID +' input.active-input').val() || 0.00)
        var NewQty = parseFloat(CurrentQty - 1.00).toFixed(3)
        $('div#'+ ProdID +' input.active-input').each(function(e){
            if (NewQty > 0) { $(this).attr('value', NewQty).val(NewQty).change(); }
            else { $(this).attr('value', 0.00).val(0.000).change();}
        })
        //UpdateCombinationPrice(ProdID, NewQty);TODO: open later
    });
    // For change in the quantity - manual edit (not from the button): TODO:open later with price
    /*$('.quantity-part #input.active-input').change(function(){
        var ProdID = $(this).attr('id')
        var NewQty = parseFloat($('div#'+ ProdID +' input.active-input').val())
        UpdateCombinationPrice(ProdID, NewQty);
    })*/
    function UpdateCombinationPrice(ProdID, NewQty){
        var parentCombination = $('body').find('ul[data-attribute_exclusions]').data('attribute_exclusions').parent_combination;
        return ajax.jsonRpc('/sale/get_combination_info', 'call', {
            'product_template_id': $('div#'+ ProdID +' input.active-input').attr('tmpl-id'),
            'product_id': $('div#'+ ProdID +' input.active-input').attr('product-id'),
            'combination': [],
            'add_qty': NewQty,
            'pricelist_id': $('div#'+ ProdID +' input.active-input').attr('pricelist-id'),
            'parent_combination': [],
        }).then(function (combinationData) {
            console.log('Combination price for selected QTY,', combinationData);
        });
    }
    // ##################### +, - ICONS CLICK ENDS ###########################################

    // Highlighting respective quantity input box
    $(document).on('click', '.qty-conversion', function (e) {
        var CurrID = $(this)[0].id;
        $('div#'+ $(this).attr('product-id')+'.left-qty-input').find('input').each(function(){
            if ($(this)[0].id == CurrID){ $(this).addClass('active-input') }
            else { $(this).removeClass('active-input') }
        })
    });

    //  ###################### UNITS CONVERSION STARTS ############################
    $(document).on('change', '.qty-conversion', function () { // Works for all conversions - single function multi use

        var ProdID = $(this).attr('product-id')
        var QtyVal = $(this).val() || 0

        // Making sure values are retained as per the data type
        if ($(this).attr('data-type') == 'int'){ QtyVal = parseInt(QtyVal);  $(this).val(QtyVal); }
        else{ QtyVal = parseFloat(QtyVal); $(this).val(QtyVal.toFixed(3));}

        if (QtyVal > 0) {

            ajax.jsonRpc("/uom/conversion", 'call',{
                'product_id': parseInt(ProdID),
                'uom_id': parseInt($(this).attr('uom-id')),
                'qty': QtyVal,
            })
            .then(function (res) {
                $('div#'+ ProdID +' input').each(function(e){
                    if (parseInt($(this).attr('uom-id')) in res){
                        $(this).val(res[$(this).attr('uom-id')][1])
                    }
                })
            });
        }
        else{ // if value < 0
            $('div#'+ ProdID +' input').each(function(e){ $(this).val(0) })
        }
    });
    //  ###################### UNITS CONVERSION ENDS ##############################

    //######################## REQUEST FOR QUOTE STARTS ##########################
    $('#rfq').click(function(){
        /*var RedirectUrl = $(this).attr('redirect-url');
        if (RedirectUrl != ''){
            console.log('redirect url',RedirectUrl);
            window.location.href = '/web/login?redirect=' + RedirectUrl;
            return false;
        }*/
        var MOQ = parseFloat($('#moq').val())
        var ProdTempID = $('#ProdTempID').val()
        var UOMID = $('#uom').val()
        var SelectedQty = 0.00
        var QtyInfo = {}
        var Products = []
        var OtherProducts = []
        var VariantProducts = [] //Electricals
        var valid = true
        var Vals = {}
        var OtherVals = {}

        if ($('input#logo_attachment_base64').val())
            {OtherVals['logo_attachment'] = $('input#logo_attachment_base64').val()}
        if ($('input#logo_tagline').val())
            {OtherVals['logo_tagline'] = $('input#logo_tagline').val()}

        $('input.main-uom:visible').each(function(){SelectedQty += parseFloat($(this).val())})
        if (isNaN(SelectedQty) || SelectedQty < MOQ || SelectedQty == 0){
            valid=false;
            swal("OOPS!", `Please select Minimum order qty.`, "error");
        }

        if ($('.quantity-part-and-quantity-box:visible div.qty-box ').length != 0){ //SteelPage/similar
            $('.quantity-part-and-quantity-box:visible div.qty-box ').each(function(){
                var InputInfo = {}
                var ProdID = $(this).attr('product-id')
                $(this).find(':input').each(function(){
                    InputInfo[parseInt($(this).attr('uom-id'))] = parseFloat($(this).val())
                    if (UOMID == $(this).attr('uom-id')){
                        InputInfo['qty'] = parseFloat($(this).val())
                        InputInfo['uom_id'] = parseInt(UOMID)
                        InputInfo['attr_id'] = JSON.parse($(this).attr('uom-attr-id'))[0]
                    }
                })
                QtyInfo[parseInt(ProdID)] = InputInfo
            })
            Products.push(QtyInfo)
        }

        if ($('.cement-qty-box tr:visible.variant-row').length != 0){ //CementMainBrand / SimilarViews
            $('.cement-qty-box tr:visible.variant-row').each(function(){
                var tds = $(this).find("td:visible:not(.deleteBrand)")
                var qty = parseInt($(this).find("td:visible.quantitytd input").val())
                if (qty > 0){
                    QtyInfo[parseInt($(this).attr('variant-id') || $(this).attr('id'))] = {'qty': qty,
                    'uom_id':$(this).attr('uom-id')}
                }
                else{
                    valid=false;
                    swal("OOPS!", `Please select Quantity.`, "error");

                }
            })
            Products.push(QtyInfo)
        }

        if ($('.cement-qty-box tr:visible.other-cement-products').length != 0){// AddBrands products
            $('.cement-qty-box tr:visible.other-cement-products').each(function(){
                var tds = $(this).find("td:visible:not(.deleteBrand)")
                var attrs = []
                tds.slice(0,tds.length-1).each(function(){
                    attrs.push($(this).attr('attr-id'))
                })
                if ($(this).hasClass('other-variant-products')){
                    VariantProducts.push({'attrs': attrs, 'qty': tds.last().find('input').val()})
                }
                else{
                    OtherProducts.push({'attrs': attrs, 'qty': tds.last().find('input').val()})
                }
            });
        }

        /* Bulk Cement Vals starts */
        if ($('body div').hasClass('cementbulkenquiry')){
            if ($('input#gstin_attachment_base64').val()){
                Vals['gst_base64'] = $('input#gstin_attachment_base64').val();
                Vals['gst_attach_name']=$('input#gstin_attachment').val();
            }

            $('.cementbulkenquiry-vals input').each(function(){

                if ($('#gstin_attachment_base64').val()){
                    Vals['gst_base64'] = $('#gstin_attachment_base64').val()
                    Vals['gst_attach_name'] = $('#gstin_attachment').val()
                }
                if ($('input#project-type').val()){
                    $('#error_project-type').html(''); Vals['project_type'] = $('input#project-type').val()
                }else{ valid=false;$('#error_project-type').html('Please enter project type.')}

                if ($('input#total-requirement').val()){
                    $('#error_total-requirement').html(''); Vals['total_requirement'] = $('input#total-requirement').val()
                }else{ valid=false;$('#error_total-requirement').html('Please enter total requirement.')}

                if ($('input#monthly-requirement').val()){
                    $('#error_monthly-requirement').html(''); Vals['monthly_requirement'] = $('#monthly-requirement').val()
                }else{ valid=false;$('#error_monthly-requirement').html('Please enter monthly requirement.')}

                if ($('input#current-requirement').val()){
                    $('#error_current-requirement').html(''); Vals['current_requirement'] = $('#current-requirement').val()
                }else{ valid=false;$('#error_current-requirement').html('Please enter current requirement.')}

                if ($('input#approved-brands').val()){
                    $('#error_approved-brands').html(''); Vals['approved_brands'] = $('#approved-brands').val()
                }else{ valid=false;$('#error_approved-brands').html('Please enter approved brands.')}

                if ($('input#contact-name').val()){
                    $('#error_contact-name').html(''); Vals['contact_name'] = $('#contact-name').val()
                }else{ valid=false;$('#error_contact-name').html('Please enter contact name.')}

                if ($('input#phone-number').val()){
                    $('#error_phone-number').html(''); Vals['phone_number'] = $('#phone-number').val()
                }else{ valid=false;$('#error_phone-number').html('Please enter phone number.')}

                if ($('input#email').val()){
                    $('#error_email').html(''); Vals['email'] = $('#email').val()
                }else{ valid=false;$('#error_email').html('Please enter email address.')}

                if ($('input#delivery-address').val()){
                    $('#error_delivery-address').html(''); Vals['delivery_address'] = $('#delivery-address').val()
                }else{ valid=false;$('#error_delivery-address').html('Please enter delivery address.')}

                if ($('input#landmark').val()){
                    $('#error_landmark').html(''); Vals['landmark'] = $('#landmark').val()
                }else{ valid=false;$('#error_landmark').html('Please enter landmark.')}

                if ($('input#city').val()){
                    $('#error_city').html(''); Vals['city'] = $('#city').val()
                }else{ valid=false;$('#error_city').html('Please enter city.')}

                if ($('input#pincode').val()){
                    $('#error_pincode').html(''); Vals['pincode'] = $('#pincode').val()
                }else{ valid=false;$('#error_pincode').html('Please enter pincode.')}

                if ($('#registered-address').val()){
                    $('#error_registered-address').html(''); Vals['registered_address'] = $('#registered-address').val()
                }else{ valid=false;$('#error_registered-address').html('Please enter your registered address.')}

                if ($('#state').val()){
                    $('#error_state').html(''); Vals['state_id'] = parseInt($('#state').val())
                }else{ valid=false;$('#error_state').html('Please select state.')}

                if ($('#district').val()){
                    $('#error_district').html(''); Vals['district'] = parseInt($('#district').val())
                }else{ valid=false;$('#error_district').html('Please select district.')}

                if ($('#gstin').val()){
                    var GST = $('#gstin').val()
                    if ((GST.length != 15) || (!GSTRegex.test(GST))) {
                        $('#error_gstin').html("Please enter a valid GSTIN.").show();
                        valid=false;
                    } else {
                        $('#error_gstin').html('').hide();
                        Vals['gstin'] = $('#gstin').val()
                    }
                }else{ valid=false;$('#error_gstin').html('Please enter your GSTIN.')}

            })
        }
        /* Bulk Cement Vals ends */

        // Create Quotation
        if (valid){
            var RFQData = {'main_product': Products,
                        'product_template': parseInt(ProdTempID),
                        'other_products': OtherProducts,
                        'variant_products': VariantProducts,
                        'hamali_charges': $('#unloadingAtSite:checked').val() || false,
                        'transport_charges': $('#transport2site:checked').val() || false,
                        'requested_del_date': $('#requested_del_date').val(),
                        'reqested_delivery_slot': $("input[name='reqested_delivery_slot']:checked").val(),
                        'bulkenq_vals': Vals,
                        'other_vals': OtherVals}
            if (session['user_id'] == false){
                sessionStorage['RFQData'] = JSON.stringify(RFQData)
                var str = jQuery.param( JSON.stringify(RFQData) );
                var attribute_qty = []
                $.map(RFQData['main_product'][0], function(value,key){
                	attribute_qty.push(key+'_'+value['qty'])
                });
                var pin = $('#pincode-serv-value').val()
                var delivery_date = RFQData['requested_del_date']
                var hamali_charges = RFQData['hamali_charges']
                var transport_charges = RFQData['transport_charges']
                var reqested_delivery_slot = RFQData['reqested_delivery_slot']
                var url_qry_str =  window.location.search
                if(window.location.search){
                	var qs = url_qry_str + '&rfq_data='+attribute_qty+ '&rfq_date='+delivery_date+ '&pin='+pin + '&hamali_charges='+hamali_charges + '&transport_charges='+transport_charges+'&reqested_delivery_slot='+reqested_delivery_slot
                	window.history.replaceState(null, null, qs);
                }else{
                	var qs =  '?rfq_data='+attribute_qty+ '&rfq_date='+delivery_date+ '&pin='+pin + '&hamali_charges='+hamali_charges + '&transport_charges='+transport_charges+'&reqested_delivery_slot='+reqested_delivery_slot
                	window.history.replaceState(null, null, qs);
                }

                sessionStorage['RedirectingURL'] = window.location.href || '/';
//                swal("OOPS!", "Please login.", "warning", button: "Login",).then((ok) => {
//                  if (ok) {window.location = '/web/login'}
//                });
                swal({
                    title: "OOPS!",
                    text: "Please login!",
                    type: "warning",
                    button: "Login",
                    icon: "warning",
                }).then(function() {
                    window.location = '/web/login';
                });
            }
            else{
                $('#rfq').hide();
                $('#rfqLoading').show();
                ajax.jsonRpc("/create/rfq", 'call',RFQData)
                .then(function (res) {
                    if (res){
                        swal("Success!", "Your RFQ has been created successfully. Please check after 15 minutes to get the updated prices.", "success").then((ok) => {
                          if (ok) {
                            $('#rfq').hide();
                            $('#rfqLoading').hide();
                            if (window.location.href.includes('?')){window.location.href = window.location.href + '&source=' + res}
                            else{window.location.href = window.location.href + '?source=' + res}
                          }
                        });
                    }
                    else{
                        $('#rfq').show();
                        $('#rfqLoading').hide();
                        swal("OOPS!", `Something went wrong.`, "error");
                    }
                });
            }
        }
    });

    $('#pdp_cancel_so').click(function(){
        rpc.query({
            model: 'sale.order',
            method: 'write',
            args: [parseInt($(this).attr('so-id')), {
                'state': 'cancel',
            }],
        }).then(function(){location.reload(true)});
    });
     $('#pdp_reset_so').click(function(){
        rpc.query({
            model: 'sale.order',
            method: 'write',
            args: [parseInt($(this).attr('so-id')), {
                'state': 'draft',
            }],
        }).then(function(){location.reload(true)});
    });


//    $('#rfq-process #confirm-rfq-so').click(function(){
//        var SaleOrder = $('#confirm-rfq-so').attr('order-ids')
//        ajax.jsonRpc("/accept/so", 'call', {'order_ids': SaleOrder})
//        .then(function (res) {
//            swal("Success!", "Thankyou for accepting the order!", "success").then((ok) => {
//              if (ok) {location.reload(true);}
//            });
//        });
//    })
//    $('#modal_reject_so #sumbit_so_rejection').click(function(){
//        var RejectInfo = $('#modal_reject_so #reject_info').val()
//        var RejectReasonID = $('#modal_reject_so #reject_reason option:selected').attr('id')
//        ajax.jsonRpc("/reject/so", 'call', {'order_id': parseInt($('#reject_rfq_so').attr('order-id')),
//        'reason_id':RejectReasonID, 'reason':RejectInfo})
//        .then(function (res) {
//            swal("Success!", "Your order has been rejected successfully!", "success").then((ok) => {
//              if (ok) {location.reload(true);}
//            });
//        })
//    })

    $('#so_add_to_cart').click(function(){
        rpc.query({
            model: 'sale.order',
            method: 'write',
            args: [JSON.parse($(this).attr('order-ids')), {
                'show_in_cart':true,
            }],
        }).then(function(){window.location.href = '/shop/cart'});
    })
	//############### wishlist #####################
	
	$('.wishlist').click(function(){
        rpc.query({
            model: 'customer.wishlist',
            method: 'add_remove_Wishlist',
            args: [{'so_name':$('.so_name').text().trim(),'product_templ_id':parseInt($('#wish_pro').text())}],
        }).then(function(res){
            if (res){$('.wishlist').css("color", "aqua");}
            else{$('.wishlist').css("color", "white");}
        });
    })
	
	//############# end wishlist ###########

    //######################## REQUEST FOR QUOTE ENDS ##########################


    $(".brandBtnId").click(function(){
        var AttrID = $(this).attr('id')
      $("#dropdown-brand-"+AttrID).toggle();
    });
    $(".brandsSelect").click(function(){
        var value = $(this).text();
        $('.SelectItem-'+$(this).attr('attr-id')).attr('id', $(this).attr('id')).text(value);
        $("#dropdown-brand-"+$(this).attr('attr-id')).hide();
    });

    $( "#searchInput" ).on( "keyup", function() {
        var input, filter, ul, li, a, i, div, txtValue;
        input = document.getElementById("searchInput");
        filter = input.value.toUpperCase();
        div = document.getElementById("dropdown-brand");
        a = div.getElementsByTagName("label");
        for (i = 0; i < a.length; i++) {
        txtValue = a[i].textContent || a[i].innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
          a[i].style.display = "";
        } else {
          a[i].style.display = "none";
        }
        }
    });
    $( "#searchGradeInput" ).on( "keyup", function() {
      var input, filter, ul, li, a, i, div, txtValue;
      input = document.getElementById("searchGradeInput");
      filter = input.value.toUpperCase();
      div = document.getElementById("dropdown-grade");
      a = div.getElementsByTagName("label");
      for (i = 0; i < a.length; i++) {
        txtValue = a[i].textContent || a[i].innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
          a[i].style.display = "";
        } else {
          a[i].style.display = "none";
        }
      }
    });

    $(document).click(function(e){
        if($(e.target).closest(".brandBtnId").length > 0 || $(e.target).closest("#searchInput").length > 0) {
        }else{
          $("#dropdown-brand").hide();
        }
        if($(e.target).closest("#gradeBtnId").length > 0  || $(e.target).closest("#searchGradeInput").length > 0) {
        }else{
          $("#dropdown-grade").hide();
        }

        /* Header search dropdown starts*/
        if($(e.target).closest(".dropdown-all").length > 0 ) {
        }else{
          $(".search-bar-dropdwon").hide();
        }
        /* header search ends */

         /* Header shipping address dropdown starts*/
        if($(e.target).closest("#address-set").length > 0 ) {
        }else{
          $(".address-bar-dropdwon").hide();
        }
        /* Header shipping address dropdown ends */
    });

    $("#gradeBtnId").click(function(){
      $("#dropdown-grade").toggle();
    })
    $(".gradeSelect").click(function(){
        var value = $(this).text();
        $('.gradeItem').text(value);
        $('.gradeItem').attr('grade-id', $(this).attr('grade-id'));
        $("#dropdown-grade").hide();
    });
    $('.add-brand-select').change(function(){
        var elmId = $(this).attr("id");
        if (!$(this).val()){
            $("#error_"+elmId).html("Please select value.").show();
            valid=false;
        }else{
            $("#error_"+elmId).html("").hide();
        }
    })
    $(document).on('keyup', '#Addquantity', function(e) {
        if (!$('.row-add-variant #Addquantity').val()){
            $("#error_Addquantity").html("Please select quantity").show();
        }else if($('.row-add-variant #Addquantity').val() == 0){
            $("#error_Addquantity").html("Quantity should be greater than 0!").show();
        }else{
            $("#error_Addquantity").html("").hide();
        }
    });
    var IDdynamic = 0;
    $("#addSelectedBrand").click(function(){
        IDdynamic++
        var AttrIDS = [] //TODO
        var valid = true
        $(".add-brand-select").each(function(){
            var elmId = $(this).attr("id");
            if (!$(this).val()){
                $("#error_"+elmId).html("Please select value.").show();
                valid=false;
            }else{
                $("#error_"+elmId).html("").hide();
            }
        })
        if (!$('.row-add-variant #Addquantity').val()){
            $("#error_Addquantity").html("Please select quantity").show();
            valid=false;
        }else if($('.row-add-variant #Addquantity').val() == 0){
            $("#error_Addquantity").html("Quantity should be greater than 0!").show();
            valid=false;
        }else{
            $("#error_Addquantity").html("").hide();
        }
        if(valid){
            var AttrsIDs = [];
            $(".add-brand-select").each(function(){
                var optionId = $(this).find('option:selected').attr("id");
                var attrID = $(this).find('option:selected').attr("attr-id");
                AttrsIDs.push(parseInt(optionId));
            })
            $('#addBrandModal').modal('hide');
            ajax.jsonRpc('/get/variant',"call", {'attr_ids':AttrsIDs,
                'selected_qty':$('.row-add-variant #Addquantity').val(),
                'product_tmpl_id':parseInt($(this).attr('product-id'))}).then(function(TR){
                $('#table-qty tbody tr:last').after(TR);
            })
        }
    });

    $(".delete_Sol").click(function(){
        rpc.query({
            model: 'sale.order.line',
            method: 'unlink',
            args: [parseInt($(this).attr('id'))],
        }).then(function(){location.reload();});
    })

    $("#addbrandQty").click(function(){
        $(".addbrand-table-row").toggle();
    })
    $('#table-qty').on('click', '.deleteBrand', function() {
        if (!$(this).closest('tr').hasClass('addbrand-table-row')){
            $(this).closest('tr').remove()
        }
        else{
            $(this).closest('tr').hide()
        }
    });
});


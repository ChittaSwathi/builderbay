//$(".bestproductSlider").hide();
$(".hotdeals").click(function(){
    $(".dealsSlider").show();
    $(".bestproductSlider").hide();
    $(".hotdeals h2").addClass("dealproduct-active");
    $(".bestproduct h2").removeClass("dealproduct-active");
});
$(".bestproduct").click(function(){
    $(".dealsSlider").hide();
    $(".bestproductSlider").show();
    $(".hotdeals h2").removeClass("dealproduct-active");
    $(".bestproduct h2").addClass("dealproduct-active");
});

//$(".ourbrandsSliderMain").hide();
$(".oursellers").click(function(){
    $(".sellerSliderMain").show();
    $(".ourbrandsSliderMain").hide();
    $(".oursellers h2").addClass("sellers-brands-active");
    $(".ourbrands h2").removeClass("sellers-brands-active");
});
$(".ourbrands").click(function(){
    $(".sellerSliderMain").hide();
    $(".ourbrandsSliderMain").show();
    $(".oursellers h2").removeClass("sellers-brands-active");
    $(".ourbrands h2").addClass("sellers-brands-active");
});
$(".safety-products").click(function(){
    $(".safetyproductsSliderMain").show();
    $(".safetybrandsSliderMain").hide();
    $(".safety-products h2").addClass("safety-products-active");
    $(".safety-brands h2").removeClass("safety-products-active");
});
$(".safety-brands").click(function(){
    $(".safetyproductsSliderMain").hide();
    $(".safetybrandsSliderMain").show();
    $(".safety-products h2").removeClass("safety-products-active");
    $(".safety-brands h2").addClass("safety-products-active");
});

$(".cement-brands").click(function(){
    $(".cementbrandsSliderMain").show();
    $(".steelbrandsSliderMain").hide();
    $(".cement-brands h2").addClass("cement-steel-active");
    $(".steel-brands h2").removeClass("cement-steel-active");
});
$(".steel-brands").click(function(){
    $(".cementbrandsSliderMain").hide();
    $(".steelbrandsSliderMain").show();
    $(".cement-brands h2").removeClass("cement-steel-active");
    $(".steel-brands h2").addClass("cement-steel-active");
});

//$(".dropdown-cement").hide();

$(".dropdownmain").hover(function(){
    var thisid = `${this.id}`;
    $("li#" + thisid + " .arrow-up").show();
    $('#megadropdown-'+thisid).show();
    $('.block-wrapper').show();
},function(){
    var thisid = `${this.id}`;
    $('#megadropdown-'+thisid).hide();
    $("li#" + thisid + " .arrow-up").hide();
    $('.block-wrapper').hide();
});

//$(".mobile-menu").hide();
$(".mobile-logo div i").click(function(){
    $(".mobile-menu").show();
    var left = $('.mobile-menu-under').offset().left;
    $('#wrapwrap').addClass('importantHidden');
    $(".mobile-menu-under").css({left:left}).animate({"left":"0px"}, "slow");
});
$(".go-left-mobilemenu").click(function(){
    var left = $('.mobile-menu-under').offset().left;
    $(".mobile-menu-under").css({left:left}).animate({"left":"-500px"}, "slow");
    setTimeout(function(){
        $(".mobile-menu").hide();
    },500);
    $('#wrapwrap').removeClass('importantHidden');
});
//$(".search-bar-dropdwon").hide();
$(".dropdown-all").click(function(){
    $(".search-bar-dropdwon").slideToggle();
});
$(".search-bar-dropdwon p").click(function(){
    var thisValue = $(this).html();
    var valueText = "<span class='productSelect'>"+thisValue+"</span>"
   $(".productSelect").replaceWith(valueText);
   $('#search-categ').val($(this).attr('id'));
})

$(document).ready(function() {
    $('.skeleton-row').hide();
    $('#autoSlider').show();
    $('#banner-under-buildsvuida').show();
    $('.dealsSlider').show();
    $('.ourbrandsSliderMain').show();
    $('.safetybrandsSliderMain').show();
    $('.topsellingblocksSliderMain').show();


    // banner under slides start
    var itemsMainDiv = ('.MultiCarousel');
    var itemsDiv = ('.MultiCarousel-inner');
    var itemWidth = "";

    $('.leftLst, .rightLst').click(function () {
        var condition = $(this).hasClass("leftLst");
        if (condition)
            click(0, this);
        else
            click(1, this)
    });
    ResCarouselSize();
    $(window).resize(function () {
        ResCarouselSize();
    });
    //this function define the size of the items
    function ResCarouselSize() {
        var incno = 0;
        var dataItems = ("data-items");
        var itemClass = ('.item');
        var id = 0;
        var btnParentSb = '';
        var itemsSplit = '';
        var sampwidth = $(itemsMainDiv).width();
        var bodyWidth = $('body').width();
        $(itemsDiv).each(function () {
            id = id + 1;
            var itemNumbers = $(this).find(itemClass).length;
            btnParentSb = $(this).parent().attr(dataItems);
            itemsSplit = btnParentSb.split(',');
            $(this).parent().attr("id", "MultiCarousel" + id);
            if (bodyWidth >= 1200) {
                incno = itemsSplit[3];
                itemWidth = sampwidth / incno;
            }
            else if (bodyWidth >= 992) {
                incno = itemsSplit[2];
                itemWidth = sampwidth / incno;
            }
            else if (bodyWidth >= 768) {
                incno = itemsSplit[1];
                itemWidth = sampwidth / incno;
            }
            else {
                incno = itemsSplit[0];
                itemWidth = sampwidth / incno;
            }
            $(this).css({ 'transform': 'translateX(0px)', 'width': itemWidth * itemNumbers +1});
            $(this).find(itemClass).each(function () {
                $(this).outerWidth(itemWidth);
            });

            $(".leftLst").addClass("over");
            $(".rightLst").removeClass("over");

        });
    }


    //this function used to move the items
    function ResCarousel(e, el, s) {
        var leftBtn = ('.leftLst');
        var rightBtn = ('.rightLst');
        var translateXval = '';
        var divStyle = $(el + ' ' + itemsDiv).css('transform');
        var values = divStyle.match(/-?[\d\.]+/g);
        var xds = Math.abs(values[4]);
        if (e == 0) {
            translateXval = parseInt(xds) - parseInt(itemWidth * s);
            $(el + ' ' + rightBtn).removeClass("over");

            if (translateXval <= itemWidth / 2) {
                translateXval = 0;
                $(el + ' ' + leftBtn).addClass("over");
            }
        }
        else if (e == 1) {
            var itemsCondition = $(el).find(itemsDiv).width() - $(el).width();
            translateXval = parseInt(xds) + parseInt(itemWidth * s);
            $(el + ' ' + leftBtn).removeClass("over");

            if (translateXval >= itemsCondition - itemWidth / 2) {
                translateXval = itemsCondition;
                $(el + ' ' + rightBtn).addClass("over");
            }
        }
        $(el + ' ' + itemsDiv).css('transform', 'translateX(' + -translateXval + 'px)');
    }

    //It is used to get some elements from btn
    function click(ell, ee) {
        var Parent = "#" + $(ee).parent().attr("id");
        var slide = $(Parent).attr("data-slide");
        ResCarousel(ell, Parent, slide);
    }

    // banner under slides ends

    /* auto slide start*/
    var checkAutoSlider = document.getElementById("autoSlider");
    if(checkAutoSlider !== null){
        !function(n){n.fn.multislider=function(e,t){var i,s,o,a,r,l,u,c,m,d,f,p=n(this),v=p.find(".MS-content"),g=p.find("button.MS-right"),h=p.find("button.MS-left"),A=v.find(".item:first");if("string"==typeof e)return i=e,void 0!==p.data(i)?p.data(i)():console.error("Multislider currently only accepts the following methods: next, prev, pause, play"),p;function w(n){p.hasClass("ms-PAUSE")?(p.removeClass("ms-PAUSE"),n(),p.addClass("ms-PAUSE")):n(),E()}function S(){P(),r=A.width();var n=parseInt(v.find(".item:first").css("padding-left")),e=parseInt(v.find(".item:first").css("padding-right"));0!==n&&(r+=n),0!==e&&(r+=e)}function C(){f=setInterval(function(){p.hasClass("ms-PAUSE")||u()},m.interval)}function E(){0!==m.interval&&!1!==m.interval&&!0!==m.continuous&&(clearInterval(f),C())}function P(){A=v.find(".item:first"),s=v.find(".item:last")}function U(n){p.hasClass("ms-animating")||p.hasClass("ms-HOVER")||p.hasClass("ms-PAUSE")||(p.trigger("ms.before.animate"),p.addClass("ms-animating"),n())}function y(){p.hasClass("ms-animating")&&(p.removeClass("ms-animating"),p.trigger("ms.after.animate"))}function b(){o=v.width(),a=Math.floor(o/r)}function M(){U(function(){P(),function(){d=m.duration;var n=parseFloat(v.find(".item:first").css("margin-left"));d*=1-n/-(r-1)}(),A.animate({marginLeft:-(r+1)},{duration:d,easing:"linear",complete:function(){A.insertAfter(s).removeAttr("style"),y(),M()}})})}function x(){U(function(){P(),b();var e=v.children(".item").clone().splice(0,a);v.append(e),A.animate({marginLeft:-o},{duration:d,easing:"swing",complete:function(){n(v.children(".item").splice(0,a)).remove(),y()}})})}function B(){U(function(){P(),b();var e=v.children(".item").length,t=v.children(".item").clone().splice(e-a,e);n(n(t)[0]).css("margin-left",-o),v.prepend(t),P(),A.animate({marginLeft:0},{duration:d,easing:"swing",complete:function(){e=v.find(".item").length,n(v.find(".item").splice(e-a,e)).remove(),A.removeAttr("style"),y()}})})}function L(){U(function(){P(),A.animate({marginLeft:-r},{duration:d,easing:"swing",complete:function(){A.detach().removeAttr("style").appendTo(v),y()}})})}function I(){U(function(){P(),s.css("margin-left",-r).prependTo(v),s.animate({marginLeft:0},{duration:d,easing:"swing",complete:function(){s.removeAttr("style"),y()}})})}return"object"!=typeof e&&void 0!==e||(v.contents().filter(function(){return 3==this.nodeType&&!/\S/.test(this.nodeValue)}).remove(),c=m||{continuous:!1,slideAll:!1,interval:2e3,duration:500,hoverPause:!0,pauseAbove:null,pauseBelow:null},m=n.extend({},c,e),S(),d=m.duration,m.hoverPause&&(m.continuous?(v.on("mouseover",function(){y(),v.children(".item:first").stop()}),v.on("mouseout",function(){M()})):(v.on("mouseover",function(){p.addClass("ms-HOVER")}),v.on("mouseout",function(){p.removeClass("ms-HOVER")}))),!0!==m.continuous&&0!==m.interval&&!1!==m.interval&&!1!==m.autoSlide&&C(),null!==m.pauseAbove&&"number"==typeof m.pauseAbove&&(window.innerWidth>m.pauseAbove&&p.addClass("ms-PAUSE"),n(window).on("resize",function(){window.innerWidth>m.pauseAbove?p.addClass("ms-PAUSE"):p.removeClass("ms-PAUSE")})),null!==m.pauseBelow&&"number"==typeof m.pauseBelow&&(window.innerWidth<m.pauseBelow&&p.addClass("ms-PAUSE"),n(window).on("resize",function(){window.innerWidth<m.pauseBelow?p.addClass("ms-PAUSE"):p.removeClass("ms-PAUSE")})),p.data({pause:function(){p.addClass("ms-PAUSE")},unPause:function(){p.removeClass("ms-PAUSE")},continuous:function(){p.removeClass("ms-PAUSE"),M()},next:function(){w(L)},nextAll:function(){w(x)},prev:function(){w(I)},prevAll:function(){w(B)},settings:m}),m.continuous?(m.autoSlide=!1,M()):m.slideAll?(l=p.data("prevAll"),u=p.data("nextAll")):(l=p.data("prev"),u=p.data("next"))),g.on("click",u),h.on("click",l),p.on("click",".MS-right, .MS-left",E),n(window).on("resize",S),p}}(jQuery);
        $('#autoSlider').multislider({
            interval: 3000,
            duration: 1500
        });
    }
    /* auto slide ends*/
})
//setTimeout(function(){
//    $(".custom-toast").fadeOut();
//}, 3000);



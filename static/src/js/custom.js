$(".dropdown-menu a").click(function () {
  $(this).parents("#Select.dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
  $(this).parents("#Select.dropdown").find('.btn').val($(this).data('value'));
});

$("#Selecttab .dropdown-menu a").click(function () {
  $(this).parents("#Selecttab.dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
  $(this).parents("#Selecttab.dropdown").find('.btn').val($(this).data('value'));
});


$(function() {
  var $btn = $('.bs-product-nav span');
  var $vlinks = $('.bs-product-nav .links');
  var $hlinks = $('.bs-product-nav .hidden-links');

  var numOfItems = 0;
  var totalSpace = 0;
  var closingTime = 1000;
  var breakWidths = [];

  // Get initial state
  $vlinks.children().outerWidth(function(i, w) {
    totalSpace += w;
    numOfItems += 1;
    breakWidths.push(totalSpace);
  });

  var availableSpace, numOfVisibleItems, requiredSpace, timer;

  function check() {

    // Get instant state
    availableSpace = $vlinks.width() - 10;
    numOfVisibleItems = $vlinks.children().length;
    requiredSpace = breakWidths[numOfVisibleItems - 1];

    // There is not enought space
    if (requiredSpace > availableSpace) {
      $vlinks.children().last().prependTo($hlinks);
      numOfVisibleItems -= 1;
      check();
      // There is more than enough space
    } else if (availableSpace > breakWidths[numOfVisibleItems]) {
      $hlinks.children().first().appendTo($vlinks);
      numOfVisibleItems += 1;
      check();
    }
    // Update the button accordingly
    $btn.attr("count", numOfItems - numOfVisibleItems);
    if (numOfVisibleItems === numOfItems) {
      $btn.addClass('hidden');
    } else $btn.removeClass('hidden');
  }

  // Window listeners
  $(window).resize(function() {
    check();
  });

  $btn.on('click', function() {
    $hlinks.toggleClass('hidden');
    clearTimeout(timer);
  });

  $hlinks.on('mouseleave', function() {
    // Mouse has left, start the timer
    timer = setTimeout(function() {
      $hlinks.addClass('hidden');
    }, closingTime);
  }).on('mouseenter', function() {
    // Mouse is back, cancel the timer
    clearTimeout(timer);
  })

  check();

});
$(function() {
  'use strict';
  /*Activate default tab contents*/
  var leftPos, newWidth, $magicLine;

  $('.bs-dropdown-tab').append("<div id='magic-line'></div>");
  $magicLine = $('#magic-line');
  $magicLine.width($('.active').width())
    .css('left', $('.active a').position().left)
    .data('origLeft', $magicLine.position().left)
    // .data('origWidth', $magicLine.width());

  $('.links li').click(function() {
    var $this = $(this);
    $this.parent().addClass('active').siblings().removeClass('active');
    $magicLine
      .data('origLeft', $this.position().left)
      // .data('origWidth', $this.parent().width());
    return false;
  });

  /*Magicline hover animation*/
  $('.links').find('li').hover(function() {
    var $thisBar = $(this);
    leftPos = $thisBar.position().left;
    newWidth = $thisBar.parent().width();
    $magicLine.css({
      "left": leftPos,
      // "width": newWidth
    });
  }, function() {
    $magicLine.css({
      "left": $magicLine.data('origLeft'),
      // "width": $magicLine.data('origWidth')
    });
  });
});
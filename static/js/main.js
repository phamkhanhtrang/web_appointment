(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();
    
    
    // Initiate the wowjs
    new WOW().init();


    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 40) {
            $('.navbar').addClass('sticky-top');
        } else {
            $('.navbar').removeClass('sticky-top');
        }
    });
    
    // Dropdown on mouse hover
    const $dropdown = $(".dropdown");
    const $dropdownToggle = $(".dropdown-toggle");
    const $dropdownMenu = $(".dropdown-menu");
    const showClass = "show";
    
    $(window).on("load resize", function() {
        if (this.matchMedia("(min-width: 992px)").matches) {
            $dropdown.hover(
            function() {
                const $this = $(this);
                $this.addClass(showClass);
                $this.find($dropdownToggle).attr("aria-expanded", "true");
                $this.find($dropdownMenu).addClass(showClass);
            },
            function() {
                const $this = $(this);
                $this.removeClass(showClass);
                $this.find($dropdownToggle).attr("aria-expanded", "false");
                $this.find($dropdownMenu).removeClass(showClass);
            }
            );
        } else {
            $dropdown.off("mouseenter mouseleave");
        }
    });
    
    
    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 100) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });


    // Date and time picker
    $('.date').datetimepicker({
        format: 'L'
    });
    $('.time').datetimepicker({
        format: 'LT'
    });


    // Image comparison
    $(".twentytwenty-container").twentytwenty({});


    // Price carousel
    $(".price-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        margin: 45,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ],
        responsive: {
            0:{
                items:1
            },
            768:{
                items:2
            }
        }
    });


    // Testimonials carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        items: 1,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ],
    });
    
})(jQuery);

const dateContainer = document.getElementById('dateContainer');
const timeContainer = document.getElementById('timeContainer');

const today = new Date();
let selectedTimeBtn = null;

// Tạo 7 ngày kế tiếp
for (let i = 0; i < 7; i++) {
  const date = new Date();
  date.setDate(today.getDate() + i);

  const day = date.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
  const number = date.getDate();

  const btn = document.createElement('div');
  btn.className = 'date';
  btn.innerHTML = `<div>${day}</div><div>${number}</div>`;
  btn.dataset.date = date.toISOString();

  btn.addEventListener('click', () => {
    document.querySelectorAll('.date').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    showTimeSlots(new Date(btn.dataset.date));
  });

  if (i === 0) btn.classList.add('selected');
  dateContainer.appendChild(btn);
}

// Tạo khung giờ từ 08:00 đến 16:00
function showTimeSlots(date) {
  timeContainer.innerHTML = '';
  const currentHour = today.getDate() === date.getDate() ? today.getHours() : 0;

  for (let hour = 8; hour <= 15; hour++) {
    if (date.getDate() === today.getDate() && hour < currentHour) continue;

    const time = document.createElement('div');
    time.className = 'time';
    const display = new Date(date);
    display.setHours(hour, 0);

    time.textContent = display.toLocaleTimeString('en-US', {
      hour: '2-digit', minute: '2-digit', hour12: true
    });

    time.addEventListener('click', () => {
      if (selectedTimeBtn) selectedTimeBtn.classList.remove('selected');
      time.classList.add('selected');
      selectedTimeBtn = time;
    });

    timeContainer.appendChild(time);
  }
}

// Mặc định chọn hôm nay
showTimeSlots(today);

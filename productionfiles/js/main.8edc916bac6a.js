console.log("Đã load file JS thành công!");

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

 const schedules = window.schedules;
console.log("Schedules:", schedules);


const dateContainer = document.getElementById('dateContainer');
const timeContainer = document.getElementById('timeContainer');
const appointmentInput = document.getElementById('appointment_time');

let selectedDate = null;
let selectedTime = null;
let selectedTimeBtn = null;



const today = new Date();

function showTimeSlots(date) {
  timeContainer.innerHTML = '';

  const isoDate = date.toISOString().split('T')[0];
  const schedule = schedules.find(s => s.date === isoDate);

  if (!schedule || schedule.status !== "work") {
    timeContainer.innerHTML = "<div>Bác sĩ nghỉ hoặc không có lịch</div>";
    return;
  }

  const booked = schedule.booked_times; 

  for (let hour = 7; hour <= 16; hour++) {
    if (hour >= 12 && hour < 13) continue;

    const timeStr = hour.toString().padStart(2, "0") + ":00";

    const btn = document.createElement('div');
    btn.className = 'time-button';
    btn.textContent = `${timeStr} - ${hour+1}:00`;

    if (booked.includes(timeStr)) {
      btn.classList.add('disabled');
      btn.style.color = "gray";
    } else {
      btn.addEventListener('click', () => {
        if (selectedTimeBtn) selectedTimeBtn.classList.remove('selected');
        btn.classList.add('selected');
        selectedTimeBtn = btn;
        selectedTime = timeStr;
        updateAppointmentTime();
      });
    }

    timeContainer.appendChild(btn);
  }
}
function countTimeSlots(date) {
  const currentHour = today.toDateString() === date.toDateString() ? today.getHours() : 0;
  let count = 0;
  for (let hour = 7; hour <= 16; hour++) {
    if (hour >= 12 && hour < 13) continue; // bỏ giờ nghỉ trưa
    if (date.toDateString() === today.toDateString() && hour < currentHour) continue;
    count++;
  }
  return count;
}

// Hiển thị 5 ngày liên tiếp
for (let i = 0; i < 5; i++) {
  const date = new Date();
  date.setDate(today.getDate() + i);

  const isoDate = date.toISOString().split('T')[0]; // YYYY-MM-DD
  const dayLabel = date.toLocaleDateString('vi-VN', {
    weekday: 'short',
    day: '2-digit',
    month: '2-digit'
  });

  const schedule = schedules.find(s => s.date === isoDate);

  const btn = document.createElement('div');
  btn.className = 'day-button';
  btn.dataset.date = isoDate;

  if (schedule) {
    if (schedule.status === "work") {
      const slotsCount = countTimeSlots(date);
      btn.innerHTML = `
        <div>${dayLabel}</div>
        <div style="font-size:12px; color:green">${slotsCount} khung giờ</div>`;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.day-button').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedDate = btn.dataset.date;
        showTimeSlots(date);
        updateAppointmentTime();
      });
    } else {
      btn.innerHTML = `
        <div>${dayLabel}</div>
        <div style="font-size:12px; color:red">Bác sĩ nghỉ</div>`;
    }
  } else {
    btn.innerHTML = `
      <div>${dayLabel}</div>
      <div style="font-size:12px; color:gray">Không có lịch</div>`;
  }

  if (i === 0) {
    btn.classList.add('selected');
    selectedDate = isoDate;
    if (schedule && schedule.status === "work") {
      showTimeSlots(date); // load times cho ngày đầu tiên
    }
  }

  dateContainer.appendChild(btn);
}

function updateAppointmentTime() {
  if (selectedDate && selectedTime) {
    const [year, month, day] = selectedDate.split("-");
    const formatted = `${selectedTime} - ${day}/${month}/${year}`;
    appointmentInput.value = formatted;
    console.log("Cập nhật appointment_time:", formatted);
  }
}

function initMap() {
    var location = { lat: 21.028511, lng: 105.804817 }; // Ví dụ: Hà Nội
    var map = new google.maps.Map(document.getElementById("map"), {
      zoom: 15,
      center: location,
    });
    var marker = new google.maps.Marker({
      position: location,
      map: map,
      title: "Địa chỉ của chúng tôi"
    });
  }

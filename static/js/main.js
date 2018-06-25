function getCookie(name) {
         var cookieValue = null;
         if (document.cookie && document.cookie != '') {
             var cookies = document.cookie.split(';');
             for (var i = 0; i < cookies.length; i++) {
                 var cookie = jQuery.trim(cookies[i]);
             if (cookie.substring(0, name.length + 1) == (name + '=')) {
                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                 break;
             }
         }
     }
     return cookieValue;
 }

$(document).ready(function() {
    $(".date_input").calendar({
        type: 'date',
        monthFirst: false,
        firstDayOfWeek: 1,
        formatter: {
            date: function (date, settings) {
                if (!date) return '';
                var day = date.getDate() + '';
                if (day.length < 2) {
                    day = '0' + day;
                }
                var month = (date.getMonth() + 1) + '';
                if (month.length < 2) {
                    month = '0' + month;
                }
                var year = date.getFullYear();
                return month + '/' + day + '/' + year;
            }
        }
    });

    $.ajaxSetup({ 
     beforeSend: function(xhr, settings) {
         if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
             xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
         }
     }
    });

    $(".ui.dropdown").dropdown();

    $(".friends_toggle").click(function() {
        $(this).toggleClass("outline");
        var act = true;
        if ($(this).hasClass("outline")) {
            act = false;
        }
        $.post({
            url: "/friends/", 
            data: {
                "friend_id": $(this).attr("friend_id"),
                "add": act
            }
        });
    });

});
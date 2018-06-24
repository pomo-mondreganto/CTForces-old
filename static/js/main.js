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
    if ( $('[type="date"]').prop('type') != 'date' ) {
        $('[type="date"]').datepicker();
    }

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
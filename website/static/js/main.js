$.ajaxSetup({ 
 beforeSend: function(xhr, settings) {
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
     if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
         xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
     }
 }
});

$(".friends_toggle_star").click(function() {
	$(this).toggleClass("fa");
	$(this).toggleClass("far");
	var act = true;
	if ($(this).hasClass("far")) {
		act = false;
	}
	$.post({
		url: "/friends/", 
		data: {
			"friend_id": $(this).attr("friends_friend_id"),
			"add": act
		}
	});
});

$("#settings_load_avatar").click(function() {
    $("#settings_load_avatar_input").click();
});

$(document).ready(function() {
    if ( $('[type="date"]').prop('type') != 'date' ) {
        $('[type="date"]').datepicker();
    }
});

$(".find_user_sidebar_input_field").on("input", function() {
    $.get({
        url: "/search_users/",
        data: {
            "username": $(".find_user_sidebar_input_field").val()
        },
        success: function(data) {
            var users = data["objects"];
            var current = $(".find_user_sidebar_input_field").val();
            if (users.length == 0 || (users.length == 1 && users[0] == current)) {
                $(".find_user_hint_table").hide();
            }
            else {
                $(".find_user_hint_table > tbody").empty();
                for (var i = 0; i < users.length; i += 1) {
                    $(".find_user_hint_table > tbody:last-child").append('<tr><td class="find_user_hint_table_td" user="' + users[i] + '">' + users[i] + '</td></tr>');
                }
                $(".find_user_hint_table").show();
            }
        },
        error: function(status, exception) {
             $(".find_user_hint_table").hide();
        }
    });
});

$(".find_user_sidebar_input_field").keyup(function(event) {
    if (event.keyCode === 13) {
        $(".find_user_sidebar_button").click();
    }
});

$(".find_user_hint_table").on("click", "td", function() {
    $(".find_user_sidebar_input_field").val($(this).attr("user"));
    $(".find_user_sidebar_input_field").trigger("input");
});

$(".find_user_sidebar_button").click(function() {
    $(location).attr("href", "/user/" + $(".find_user_sidebar_input_field").val() + "/");
});
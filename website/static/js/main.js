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
         xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
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
	$.post(
		"/friends/", 
		{
			"friend_id": $(this).attr("friends_friend_id"),
			"add": act
		},
		function(){}
	);
});

$("#friends_form").submit(function() {
	
});
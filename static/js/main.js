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
    if ($(".post_create_textarea").length) {
        var post_create_textarea_mde = new SimpleMDE({ element : $(".post_create_textarea")[0] });
    }

    if ($(".comment_create_textarea").length) {
        var comment_create_textarea_mde = new SimpleMDE({ element : $(".comment_create_textarea")[0] });
    }




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

    $(".post_comment_button").click(function() {
        var add = $(this).parent().next().attr("class") != "post_comment_reply_form";
        $(".post_comment_reply_form").remove();
        if (add) {
            $(this).parent().after(
                    '<div class="post_comment_reply_form">' +
                        '<form method="post" action="/leave_comment/">' + 
                            '<input type="hidden" name="csrfmiddlewaretoken" value="' + getCookie("csrftoken") + '">' +
                            '<textarea name="text" class="comment_create_textarea">' + 
                            '</textarea>' + 
                            '<div class="post_comment_submit_div">' +
                                '<input type="submit" value="Post"/>' + 
                            '</div>' +
                        '</form>' + 
                    '</div>'
                    );
            var comment_create_textarea_mde = new SimpleMDE({ element : $(".comment_create_textarea")[0] });
        }
    });


    $.ajaxSetup({ 
     beforeSend: function(xhr, settings) {
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
        $(".file_upload_error").remove();
        $("#settings_load_avatar_input").click();
    });

});
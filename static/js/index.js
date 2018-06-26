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

 var md;
 var mk;
 var SimpleMDE = require("simplemde");
 var hljs = require('highlight.js');

 function buildMDE() {
    $(".mdeditor").each(function(index) {
            var mde = new SimpleMDE({ element : $(".mdeditor")[index], spellChecker: false, previewRender: function(plainText) {
                return md.render(plainText);
            }
        });
        $(this).data("mde", mde);
    });
 }

 function updateMDE() {
    $(".mdeditor").each(function(index) {
        $(this).val($(this).data("mde").value());
    });
 }

 $(document).ready(function() {
    editors = [];
    md = require('markdown-it')({
        typographer: true,
        linkify: true,
        highlight: function (str, lang) {
            if (lang && hljs.getLanguage(lang)) {
              try {
                return hljs.highlight(lang, str).value;
              } catch (__) {}
            }

            return '';
          }
    }).use(require('markdown-it-katex'))
      .use(require('markdown-it-sub'))
      .use(require('markdown-it-sup'))
      .use(require('markdown-it-emoji'));
    $(".markdown").each(function(index) {
        $(this).addClass("markdown-body");
        $(this).html(md.render($.trim($(this).text())));
    });
    hljs.initHighlightingOnLoad();
    buildMDE();
});

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
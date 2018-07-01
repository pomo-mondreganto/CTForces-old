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

 import '../semantic/dist/semantic.min.css';
 import '../css/main.css';
 import '../css/jquery-ui.css';
 import '../css/simplemde.min.css';
 import '../css/jquery.tagit.css';
 import '../css/tagit.ui-zendesk.css';
 import '../css/ranks.css';
 import '../css/calendar.min.css';
 import '../css/github-markdown.min.css';
 import '../css/katex.min.css';
 import '../img/favicon.png';
 

 window.$ = require('jquery');
 window.jQuery = window.$;
 require('jquery-ui/ui/core.js');
 require('jquery-ui/ui/widget.js');
 require('jquery-ui/ui/position.js');
 require('jquery-ui/ui/widgets/autocomplete.js');

 require('semantic-ui-calendar/dist/calendar.min.js');

 require('../semantic/dist/semantic.min.js');
 require('./jquery.fileupload.js');
 require('./jquery.iframe-transport.js');
 require('./tag-it.js');


 var md;
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
    }).use(require('./md-it-katex'))
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

    $(".datetime_input").calendar({
        type: 'datetime',
        monthFirst: false,
        firstDayOfWeek: 1,
        ampm: false,
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
         xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
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
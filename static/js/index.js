import 'jquery-ui-dist/jquery-ui.css';
import 'simplemde/dist/simplemde.min.css';
import 'semantic-ui-calendar/dist/calendar.min.css';
import 'katex/dist/katex.min.css';
import 'tag-it/css/jquery.tagit.css';
import 'tag-it/css/tagit.ui-zendesk.css';
import 'github-markdown-css/github-markdown.css';

import '../semantic/dist/semantic.min.css';
import '../css/main.css';
import '../css/media.css';
import '../css/ranks.css';
import '../img/favicon.png';


import $ from 'jquery';
window.jQuery = $; window.$ = $;

import 'jquery-ui-dist/jquery-ui.js';
import './tag-it_fixed';
import 'semantic-ui-calendar/dist/calendar.min.js';
import '../semantic/dist/semantic.min.js';
import './jquery.touchwipe.min.js';
import 'jquery-form';


let md;

import SimpleMDE from 'simplemde';
import hljs from 'highlight.js';
import Timer from 'easytimer.js';

export function bindTimer(object, time) {
    let time_delta = (new Date(time) - new Date()) / 1000;
    let timer = new Timer();
    timer.start({
        countdown: true,
        startValues: {
            seconds: time_delta
        }
    });
    timer.addEventListener('secondsUpdated', function(e) {
        $(object).html(
            (timer.getTimeValues()["days"] ? timer.getTimeValues()["days"] + " days " : "") +
             timer.getTimeValues().toString()
        );
    });
}

export function buildMDE() {
    $(".mdeditor").each(function(index) {
        let mde = new SimpleMDE({
            element : $(".mdeditor")[index],
            spellChecker: false,
            previewRender: function(plainText) {
                return md.render(plainText);
            }
        });

        $(this).data("mde", mde);
    });
}

export function updateMDE() {
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
                let day = date.getDate() + '';
                if (day.length < 2) {
                    day = '0' + day;
                }
                let month = (date.getMonth() + 1) + '';
                if (month.length < 2) {
                    month = '0' + month;
                }
                let year = date.getFullYear();
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
                let day = date.getDate() + '';
                if (day.length < 2) {
                day = '0' + day;
                }
                let month = (date.getMonth() + 1) + '';
                if (month.length < 2) {
                month = '0' + month;
                }
                let year = date.getFullYear();
                return month + '/' + day + '/' + year;
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

    $("#toggle_left_sidebar").click(function() {
        $("#left_sidebar").sidebar("toggle");
    });

    $("#toggle_right_sidebar").click(function() {
        $("#right_sidebar").sidebar("toggle");
    });

    $('form_init').each(function() {
        $(this).replaceWith("<script>" + $(this).html() + "</script>")
    });

});
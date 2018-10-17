
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function all(arr, condition) {
    var i = arr.length-1;
    for(;i>=0; i--) {
        if(!condition(arr[i])) {
            return false;
        }
    }

    return true;
}

function any(arr, condition) {
    var i = arr.length-1;
    for(;i>=0; i--) {
        if(condition(arr[i])) {
            return true;
        }
    }

    return false;
}

var app = angular.module('app', ['ngRoute', '720kb.datepicker'])
.config(function($routeProvider) {
    $routeProvider
        .when('/', {
            templateUrl: "/static/pages/change_log.html"
        })
        .when('/login', {
            templateUrl: "/static/pages/login.html",
            controller: "authCtrl"
        })
        .when('/group/:id/', {
            templateUrl: "static/pages/group.html",
            controller: "groupCtrl"
        })
        .when('/group/:id/:date', {
            templateUrl: "static/pages/group.html",
            controller: "groupCtrl"
        })
        .when('/sampo', {
            templateUrl: "/static/pages/sampo.html",
            controller: "sampoCtrl"
        })
});

app.filter('slice', function() {
      return function(arr, start, end) {
              return arr.slice(start, end);
            };
});

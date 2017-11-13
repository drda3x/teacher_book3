(function(window) {
    var app = angular.module('app', ['ngRoute'])
    .config(function($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: "/static/pages/page1.html"
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
    });

    app.controller('sideBarCtrl', function($scope, $http, $location) {
        $scope.groups = [];

        $http({
            method: "GET",
            url: "/groups"
        }).then(function(response) {
            $scope.groups = response.data;
        }, function(response) {
            if(response.status == 403) {
                $location.path('/login')
            }
            console.log(response);
        })
    });

    app.controller('authCtrl', function($scope, $http, $location) {
        $scope.login = function(uname, passwd) {
            $http({
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                method: "POST",
                url: "/login",
                data: {
                    username: uname,
                    password: passwd
                }
            }).then(function(response) {
                //$location.path('/');
                console.log("OK")
            }, function(response) {
                console.log("ERROR")
            }); 
        };
    });

    app.controller('groupCtrl', function($scope, $http, $location) {
        $scope.data = {};
        $http({
            method: "GET",
            url: $location.$$path
        }).then(function(response) {
            $scope.data = response.data;
        }, function(response) {
        });
    });
})(window)

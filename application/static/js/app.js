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

    app.controller('navBarCtrl', function($scope, $rootScope) {
        $scope.header = null;
        $scope.header2 = null;

        $scope.$watch('$root.header', function() {
            $scope.header = $rootScope.header;
            $scope.header2 = $rootScope.header2;
        });
    });

    app.controller('sideBarCtrl', function($scope, $http, $location) {
        $scope.groups = [];
        $scope.active = null;

        $http({
            method: "GET",
            url: "/groups"
        }).then(function(response) {
            $scope.groups = response.data;
        }, function(response) {
            if(response.status == 403) {
                $location.path('/login')
            }
        })

        $scope.$on('$locationChangeSuccess', function() {
            var path = $location.path().split('/'),
                category = path[1],
                id = parseInt(path[2]);
            
            $scope.active = id;
        });
    });

    app.controller('authCtrl', function($scope, $http, $location, $router) {
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
                $location.path('/');
                $router.reload();
            }, function(response) {
                console.log("ERROR")
            }); 
        };
    });

    app.controller('groupCtrl', function($scope, $http, $location, $rootScope) {
        $scope.data = {};
        $http({
            method: "GET",
            url: $location.path()
        }).then(function(response) {
            $scope.data = response.data;
            var group = $scope.data.group;
            $rootScope.header = group.name;
            $rootScope.header2 = group.dance_hall.station + " " + group.days + " " + group.time;
        }, function(response) {
        });
    });
})(window)

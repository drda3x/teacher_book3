(function(window) {
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
                grouter.reload();
            }, function(response) {
                console.log("ERROR")
            }); 
        };
    });

    app.controller('groupCtrl', function($scope, $http, $location, $rootScope) {
        $scope.data = {};
        $scope.main_list = [];
        $scope.sub_list = [];

        $http({
            method: "GET",
            url: $location.path()
        }).then(function(response) {

            $scope.data = response.data;
            $scope.main_list = [];
            $scope.sub_list = [];
            var group = $scope.data.group;
            $rootScope.header = group.name;
            $rootScope.header2 = group.dance_hall.station + " " + group.days + " " + group.time;
            
            for(var i=0, j=$scope.data.students.length; i<j; i++) {
                var passed = any($scope.data.students[i].lessons, function(lesson) {
                    return lesson.status != -2
                })

                if(passed){
                    $scope.main_list.push($scope.data.students[i]);
                } else {
                    $scope.sub_list.push($scope.data.students[i]);
                }
            }

        }, function(response) {
        });

        function LessonWidget() {
            this.elem = $("#lessonWidget").modal({
                show: false
            })
        }

        LessonWidget.prototype.show = function(index) {
            this.elem.modal('show');
            var data = [],
                lesson, student;
            for(var i=0, j=$scope.data.students.length; i<j; i++) {
                student = $scope.data.students[i];
                lesson = student.lessons[index];
                lesson.temp_status = lesson.status;
                
                data.push({
                    info: student.info,
                    lesson: lesson
                });
            }

            this.data = data;
            this.date = $scope.data.dates[index];
        }

        LessonWidget.prototype.process_student = function(lesson) {
            if(lesson.temp_status >= 0) {
                lesson.temp_status = (lesson.temp_status == 1) ? 0 : 1; 
            }
        }
        
        $scope.lessonWidget = new LessonWidget();

    });
})(window)

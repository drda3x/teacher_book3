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

    app.controller('authCtrl', function($scope, $http, $location, $route) {
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
                $route.reload();
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
                lesson.temp_pass = null;
                
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
                lesson.temp_status = (lesson.temp_status == 1) ? 2 : 1; 
            }
        }

        LessonWidget.prototype.save = function(attendance) {
            var data = {
                group: $scope.data.group.id,
                date: this.date,
                set_attendance: attendance,
                students: []
            };

            $.map(this.data, function(elem) {
                var d = {};
                d.stid = elem.info.id;
                d.lesson = {}; 

                d.lesson.is_new = elem.lesson.temp_pass != null;
                
                if(!d.lesson.is_new && elem.lesson.temp_status == elem.lesson.status) {
                    return
                }

                d.lesson.pass_type = (function () {
                    if(d.lesson.is_new) {
                        return parseInt(elem.lesson.temp_pass);
                    } else if (elem.lesson.temp_status != -2) {
                        return elem.lesson.group_pass.pass_type.id
                    } else {
                        return null;
                    }
                })()

                d.lesson.status = elem.lesson.temp_pass == null ? elem.lesson.temp_status : 1;

                data.students.push(d);
            });
            
            $http({
                method: "POST",
                url: '/process_lesson',
                data: data,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
            }).then(function(response) {
                console.log("OK");
            }, function(response) {
                console.log("ERROR")
            });
        }
        
        $scope.lessonWidget = new LessonWidget();

        $scope.calcLesson = function(index) {
            var lessons = [];
            var money,
                lesson;

            $.map($scope.data.students, function(student) {
                lesson = student.lessons[index]
                if(lesson.status == 1 || lesson.status == 2) {
                    money = (money || 0) + (lesson.group_pass.pass_type.prise / lesson.group_pass.pass_type.lessons);
                }
            });

            return money;
        }

        $scope.calcClub = function(index) {
            var total = $scope.calcLesson(index);
            
            if(total) {
                total -= $scope.data.group.dance_hall.prise;
                total *= 0.3;
            }

            return total
        }

        $scope.calcTotal = function(index) {
            var total = $scope.calcLesson(index);
            
            if(total) {
                total -= ($scope.data.group.dance_hall.prise + $scope.calcClub(index));
            }

            return total;
        }

    });
})(window)

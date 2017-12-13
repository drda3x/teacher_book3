(function() {
    
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
    
    // Директива для задания динамического
    // размера input'ов
    app.directive('ngSize', function(){
        return {
            restrict: 'A',
            scope: {
                size: "=ngSize",
                defaultSize: '=defaultSize'
            },
            link: function(scope, element, attrs){
                if(!element.nodeName === 'SELECT'){
                    return;
                }
    
                scope.$watch("size", function(val) {
                    attrs.$set('size', val || scope.defaultSize);	
                })
            }
        }
    })
    app.controller('navBarCtrl', function($scope, $rootScope) {
        $scope.header = null;
        $scope.header2 = null;
        $scope.user = null;
    
        $scope.$watch('$root.header', function() {
            $scope.header = $rootScope.header;
        });
    
        $scope.$watch('$root.header2', function() {
            $scope.header2 = $rootScope.header2;
        });
    
        $scope.$watch('$root.user', function() {
            $scope.user = $rootScope.user;
        });
    });
    app.controller('sideBarCtrl', function($scope, $http, $location, $rootScope) {
        $scope.elements = [];
        $scope.active = null;
        $scope.showSideBar = true;
    
        $scope.load = function() {
            $http({
                method: "GET",
                url: "/groups"
            }).then(function(response) {
                $scope.elements = response.data;
            }, function(response) {
                if(response.status == 403) {
                    $location.path('/login')
                }
            })
        }
    
        $scope.$on('$locationChangeSuccess', function() {
            var path = $location.path().split('/'),
                category = path[1],
                id = parseInt(path[2]);
            
            $scope.active = id;
            $scope.showSideBar = category !== 'login';
        });
    
        $scope.$watch('$root.showSideBar', function(val) {
            if(val == undefined) {
                return;
            }
    
            $scope.showSideBar = val;
    
            if(val) {
                $scope.load();
            }
        })
    
        $scope.load();
    });
    
    app.controller('authCtrl', function($scope, $http, $location, $window, $rootScope) {
        $rootScope.showSideBar = false;
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
                $rootScope.showSideBar = true;
                $rootScope.user = response.data;
            }, function(response) {
                console.log("ERROR")
            }); 
        };
    
        $scope.logout = function() {
            $http({
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                method: "POST",
                url: "/logout"
            }).then(function(response) {
                $rootScope.showSideBar = false;
                $rootScope.header = null;
                $rootScope.header2 = null;
                $rootScope.user = null;
                $location.path('/login');
            }, function(response) {
            });
        }
    
    
    });
    app.controller('groupCtrl', function($scope, $http, $location, $rootScope, $document, $timeout) {
        $scope.data = {};
        $scope.main_list = [];
        $scope.sub_list = [];
        $scope.selected_month = null;
    
        function fillSubLists() {
            $scope.main_list = [];
            $scope.sub_list = [];
            $.map($scope.data.students, function(student) {
                var passed = any(student.lessons, function(lesson) {
                    return lesson.status != -2;
                })
    
                if(passed) {
                    $scope.main_list.push(student);
                } else {
                    $scope.sub_list.push(student);
                }
            })
        }
        
    
        function load() {
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
                $scope.selected_month = response.data.selected_month;
                $scope.month_list = response.data.month_list;
                    
                var group = $scope.data.group;
                $rootScope.header = group.name;
                $rootScope.header2 = group.dance_hall.station + " " + group.days + " " + group.time;
    
                fillSubLists();
                getAllTeachers();
            }, function(response) {
            });
        }
    
        function getAllTeachers() {
            var teachers = {};
    
            for(var i=0, j=$scope.data.teachers.work.length; i<j; i++) {
                var list = $scope.data.teachers.work[i];
    
                for(var k=0, m=list.length; k<m; k++) {
                    teachers[list[k]] = true;
                }
            }
            
            $scope.data.teachers.cp_teachers = Object.keys(teachers);
        }
    
        function LessonWidget() {
            this.elem = $("#lessonWidget").modal({
                show: false
            });
        }
    
        $scope.checkTeacher = function(teacher) {
            return any($scope.data.teachers.cp_teachers, function(elem) {
                return elem == teacher.id;
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
            this.index = index;
            this.date = $scope.data.dates[index].val;
            this.is_canceled = $scope.data.dates[index].canceled;
            this.windowHeight = window.innerHeight;
    
            this.teachers = $.grep($scope.data.teachers.work, function(val, i) {
                return i == index;
            })[0];
    
            this.teachers = $.map(this.teachers, function(val) {
                return ""+val;
            });
    
            console.log(this.teachers);
        }
    
        LessonWidget.prototype.hide = function(lesson) {
            this.elem.modal('hide');
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
                students: [],
                teachers: this.teachers
            };
    
            $.map(this.data, function(elem) {
                var d = {};
                d.stid = elem.info.id;
                d.lesson = {}; 
    
                d.lesson.is_new = elem.lesson.temp_pass != null;
    
                if(attendance && elem.lesson.temp_status == 0) {
                    elem.lesson.temp_status = 2;
                }
                
                var check_status = elem.lesson.temp_status == elem.lesson.status;
                if(!d.lesson.is_new && check_status) {
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
            
            this.hide();
            $http({
                method: "POST",
                url: '/process_lesson',
                data: data,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
            }).then(function(response) {
                load();
            }, function(response) {
            });
        }
    
        LessonWidget.prototype.cancelLesson = function() {
            var self = this;
            self.hide();
    
            $http({
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                method: "POST",
                url: "/cancel_lesson",
                data : {
                    date: this.date,
                    group: $scope.data.group.id
                }
            }).then(function(response) {
                $scope.data.students = response.data;
                fillSubLists();
                $scope.data.dates[self.index].canceled = true; 
            }, function() {
            });
        }
    
        LessonWidget.prototype.restoreLesson = function() {
            var self = this;
            self.hide();
    
            $http({
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                method: "POST", 
                url: "/restore_lesson",
                data : {
                    date: this.date,
                    group: $scope.data.group.id
                }
            }).then(function(response) {
                $scope.data.students = response.data;
                fillSubLists();
                $scope.data.dates[self.index].canceled = true; 
            }, function() {
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
    
        $scope.calcTeacherSalary = function(teacher, index) {
            var cpt = $scope.data.teachers.work[index];
            var assist_sal = 500;
    
            function has_work_today(tid) {
                return any(cpt, function(val) {
                    return val == tid;
                });
            }
    
            if (has_work_today(teacher.id)) {
                if(teacher.assistant) {
                    return isNaN($scope.calcTotal(index)) ? '-' : assist_sal;
                } else {
                    var assists = $.grep($scope.data.teachers.list, function(t) {
                        return has_work_today(t.id) && t.assistant;
                    });
                    var sal = ($scope.calcTotal(index) - assist_sal * assists.length) / (cpt.length - assists.length);
                    return isNaN(sal) ? '-' : sal < 0 ? 0 : sal;
                }
            } else {
                return '-';
            }
        };
    
        function StudentEditWidget() {
            this.window = $('#studentEdit').modal({
                show: false
            });
    
            this.data = {
                phone: '',
                name: '',
                last_name: '',
                org_status: false,
                id: null
            };
    
            this.student = null;
            this.tab = 'info';
    
            this.editor = {
                tab: 'delete',
                data: {
                    date_0: null,
                    date_1: null,
                    date_2: null,
                    cnt: null
                }
            }
        }   
    
        StudentEditWidget.prototype.setTab = function(newTabName) {
            this.tab = newTabName;
        }
    
        StudentEditWidget.prototype.add = function() {
            var new_student = {
                info: {
                    id: null,
                    first_name: null,
                    last_name: null,
                    phone: null,
                    org: false
                },
                lessons: $.map($scope.data.dates, function(date) {
                    return {
                        status: -2,
                        date: date.val
                    }
                })
            };
    
            $scope.data.students.unshift(new_student);
            $scope.main_list.unshift(new_student);
             
            $timeout($.proxy(this.show, this), 10, true, 0, $scope.main_list);
            //this.show(0, $scope.main_list);
        }
    
        StudentEditWidget.prototype.remove = function(index, arr) {
            arr.splice(index, 1);
        }
        
        StudentEditWidget.prototype.show = function(index, arr) {
            this.clear();
            this.index = index;
    
            if(!isNaN(parseInt(index))) {
                var student = arr[index];
    
                this.data.phone = student.info.phone;
                this.data.name = student.info.first_name;
                this.data.last_name = student.info.last_name;
                this.data.org_status = student.info.org;
                this.data.id = student.info.id;
                this.student = student;
    
            }
    
            //this.window.modal('show');
            $('body').one('click', $.proxy(this.save, this));
            $('.student-edit-widget').click(function(e) {
                e.stopPropagation();
            });
        }
    
        StudentEditWidget.prototype.clear = function() {
            this.data.phone = '';
            this.data.name = '';
            this.data.last_name = '';
            this.data.org_status = false;
            this.data.id = null;
            this.student = null;
            this.index = null;
    
            this.tab = 'info';
            this.editor.tab = 'delete';
            this.editor.data = {
                date_0: null,
                date_1: null,
                date_2: null,
                cnt: null
            };
    
            $('.student-edit-widget').off('click');
        }
    
        StudentEditWidget.prototype.save = function() {
            var date = $scope.data.dates[0].val,
                self = this,
                student = self.student;
    
    
            if(!student
                    || !(!self.data.last_name || student.info.last_name == self.data.last_name)
                    || !(!self.data.name || student.info.first_name == self.data.name)
                    || !(!self.data.phone || student.info.phone == self.data.phone)
                    || !(!self.data.org_status || student.info.org == self.data.org_status))
            {
                $http({
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    method: "POST",
                    url: '/edit_student',
                    data: {
                        date: date,
                        stid: self.data.id,
                        name: self.data.name,
                        last_name: self.data.last_name,
                        phone: self.data.phone,
                        org_status: self.data.org_status,
                        group: $scope.data.group.id
                    }
                }).then(function(response) {
                    var is_new_student = student == null;
    
                    if(is_new_student) {
                        $scope.data.students.push(response.data);
                        fillSubLists();
                    } else {
                        student.info = response.data.info;
                    }
                }, function(response) {
                });
                
            } else if(!student.info.last_name && !student.info.first_name && !student.info.phone) {
                this.remove(0, $scope.main_list);
            } 
    
            this.clear();
            $scope.$apply();
        }
    
        StudentEditWidget.prototype.showMenu = function(index) {
            this.menuIndex = index;
        }
    
        StudentEditWidget.prototype.delete = function(index) {
            var self = this;
    
            $http({
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                method: "POST",
                url: "/delete_student",
                data: {
                    group: $scope.data.group.id,
                    stid: $scope.main_list[index].info.id
                }
            }).then(function() {
                self.remove(index, $scope.main_list);
            }, function() {
    
            });
        }
    
        StudentEditWidget.prototype.trash = function(index) {
            alert("Method doesn't implemented");
        }
        
        $scope.studentEditWidget = new StudentEditWidget();
    
        $scope.hideSidebar = function() {
            $rootScope.showSideBar = false;
        }
        
        $scope.showSidebar = function() {
            $rootScope.showSideBar = true;
        }
    
        $document.off('keydown');
        $document.on('keydown', function(event) {
            var localReload;
            try {
                localReload = $location.path().split('/')[1] == 'group';
            } catch(e) {
                localReload = false;
            }
    
            if(event.key == 'F5' && localReload) {
                event.preventDefault();
                load();
            }
        })
        
        $scope.$watch('selected_month', function(new_val, old_val) {
            if(new_val == undefined || old_val == undefined) {
                return;
            }
            try {
                $location.path('group/'+$scope.data.group.id+'/'+new_val);
            } catch(e) {
            }
        });
        
        $scope.sideBarIsOpened = true;
        $scope.$watch('$root.showSideBar', function(val) {
            $scope.sideBarIsOpened = val;
        });
    
        load();
    });
})()
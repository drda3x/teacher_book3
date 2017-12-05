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
    
    alertify.success("Обработка данных");

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
            alertify.success("OK")
        }, function(response) {
            alertify.error("Ошибка при загрузке страницы")
        });
    }

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
        this.index = index;
        this.date = $scope.data.dates[index].val;
        this.is_canceled = $scope.data.dates[index].canceled;
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
            students: []
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
            $.map($scope.data.students, function(student) {
                var id = parseInt(student.info.id);
                if(response.data.hasOwnProperty(id)) {
                    student.lessons = response.data[id];
                }
            });
            fillSubLists(); 
            alertify.success("Сохранено");
        }, function(response) {
            alertify.error("Ошибка в процессе сохранения");
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
            alertify.success("Сохранено");
            $scope.data.dates[self.index].canceled = true; 
        }, function() {
            alertify.error("Ошибка в процессе сохранения");
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
            alertify.success("Сохранено");
            $scope.data.dates[self.index].canceled = true; 
        }, function() {
            alertify.error("Ошибка в процессе сохранения");
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
                || !(student.info.last_name == self.data.last_name)
                || !(student.info.first_name == self.data.name)
                || !(student.info.phone == self.data.phone)
                || !(student.info.org == self.data.org_status))
        {
            alertify.message('Сохранение данных');
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
                alertify.success('Сохранено'); 
            }, function(response) {
                alertify.error('В процессе сохранения произошла ошибка'); 
            });
        } else if(student.info.last_name == null && student.info.first_name == null && student.info.phone == null) {
            this.remove();
        } 

        this.clear();
        $scope.$apply();
    }
    
    $scope.studentEditWidget = new StudentEditWidget();

    $document.off('keydown');
    $document.on('keydown', function(event) {
        var localReload;
        try {
            localReload = $location.path().split('/')[1] == 'group';
        } catch(e) {
            localReload = false;
        }

        if(event.key == 'F5' && localReload) {
            alertify.success("Перезагрузка")
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

    load();
});
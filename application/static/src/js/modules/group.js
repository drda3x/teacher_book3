// module
app.controller('groupCtrl', function($scope, $http, $location, $rootScope, $document, $timeout) {
    month = [
        '',
        'Январь',
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь"
    ]

    $scope.data = {};
    $scope.main_list = [];
    $scope.sub_list = [];
    $scope.selected_month = null;

    function sortStudentsList(student_a, student_b) {
        var str1 = student_a.info.last_name + student_a.info.first_name,
            str2 = student_b.info.last_name + student_b.info.first_name;

        if(str1 > str2) {
            return 1;
        } else if(str1 < str2) {
            return -1;
        } else {
            return 0;
        }
    }

    function fillSubLists() {
        var has_started = moment($scope.data.group.start_date, "DD.MM.YYYY") < moment();
        $scope.main_list = [];
        $scope.sub_list = [];
        
        if (!has_started) {
            $scope.main_list = $.map($scope.data.students, function(e) {return e});
        } else {
            $.map($scope.data.students, function(student) {
                var passed = any(student.lessons, function(lesson) {
                    return lesson.status != -2;
                });

                if(passed) {
                    $scope.main_list.push(student);
                } else {
                    $scope.sub_list.push(student);
                }

                $scope.main_list.sort(sortStudentsList);
                $scope.sub_list.sort(sortStudentsList);
            })
        }
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
            $rootScope.header3 = (function(teachers) {
                tmp = teachers.map(function(elem) {
                    return elem.last_name + " " + elem.first_name;
                })

                return tmp.join('-')
            })($scope.data.teachers.persons);

            fillSubLists();
            getAllTeachers();
        }, function(response) {
        });
    }

    $scope.getSellColor = function(status, lesson_color, index) {
        if($scope.data.dates[index].canceled) {
            return "#b1b3b1";
        } else {
            return status == 4 ? "inherit" : lesson_color;
        }
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

    $scope.getComment = function(student_id) {
        var comments = $scope.data.comments;

        for(var i=0, j=comments.length; i<j; i++) {
            if(comments[i].student_id == student_id) {
                return comments[i];
            }
        };

        return null;
    }

    $scope.formatPhone = function(phone) {
        if(phone.length < 10) {
            return phone
        }

        var new_phone = phone.split('');
        new_phone.splice(1, 0, '(')
        new_phone.splice(5, 0, ')')
        new_phone.splice(9, 0, '-')
        new_phone.splice(12, 0, '-')

        return "+" + new_phone.join('')
    }

    $scope.checkMoveingAbility = function(student, index) {
        return true;
        return index >= 0 && index < $scope.data.dates.length && student.lessons[index].status == -2;
    }

    $scope.deleteLesson = function(event, cur_index, student) {
        event.stopPropagation(); 

        var data = {
            date: $scope.data.dates[cur_index].val,
            count: 1,
            group: $scope.data.group.id,
            stid: student.info.id
        }

        if(!confirm("Подтвердите удаление занятия")) {
            return;
        }

        $http({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            method: "POST",
            data: data,
            url: "delete_lessons"
        }).then(function(responce) {
            load();
        }, function() {})
    }

    $scope.canEditLessons = false;
    $scope.setEditState = function(event) {
        event.stopPropagation();
        $scope.canEditLessons = true;

        $('body').click(function() {
            $scope.$apply(function() {
               $scope.canEditLessons = false;
            });
        });
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

        data.sort(sortStudentsList);

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

        $.map(this.data, $.proxy(function(elem) {
            var d = {};
            d.stid = elem.info.id;
            d.lesson = {}; 
            
            d.lesson.is_new = elem.lesson.temp_pass != null && elem.lesson.temp_pass != "-1";

            if(attendance && elem.lesson.temp_status == 0) {
                elem.lesson.temp_status = 2;
            }
            
            var cc = this.checkClubCard(d.stid);
            var check_status = elem.lesson.temp_status == elem.lesson.status && !(cc && elem.lesson.temp_pass == '-1');

            if(!d.lesson.is_new && check_status) {
                return
            }

            d.lesson.pass_type = (function () {
                if(cc) {
                    return cc.id;                    
                } else if(d.lesson.is_new) {
                    return parseInt(elem.lesson.temp_pass);
                } else if (elem.lesson.temp_status != -2) {
                    return elem.lesson.group_pass.pass_type.id
                } else {
                    return null;
                }
            })()

            d.lesson.status = (function() {
                if (cc != null || elem.lesson.temp_pass != null) {
                    return 1;
                } else if (elem.lesson.temp_pass == null) {
                    return elem.lesson.temp_status;
                }
            })()

            data.students.push(d);

        }, this));
        
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
            $scope.data.dates[self.index].canceled = false; 
        }, function() {
        });
    }

    LessonWidget.prototype.checkClubCard = function(student_id) {
        var rec, d1, d2, d3;
        for(i in $scope.data.club_cards) {
            rec = $scope.data.club_cards[i];
            d1 = moment(rec.start_date, 'dd.mm.YYYY');
            d2 = moment(rec.end_date, 'dd.mm.YYYY');
            d3 = moment(this.date, 'dd.mm.YYYY');

            if(rec.student == student_id && d1 <= d3 && d2 >= d3) {
                return rec.id;
            }
        }

        return null;
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

        return Math.round(total, 2)
    }

    $scope.calcTotal = function(index) {
        var total = $scope.calcLesson(index);
        
        if(total) {
            total -= ($scope.data.group.dance_hall.prise + $scope.calcClub(index));
        }

        return total;
    }

    $scope.calcTeacherSalary = function(teacher, index) {
        var cpt = $.grep($scope.data.teachers.work[index], function(t) {
            return t > 0
        });
        var assist_sal = 500;
        var lesson_canceled = $scope.data.dates[index].canceled;
        var lesson_moment = moment($scope.data.dates[index].val, "DD.MM.YYYY"),
            happen = lesson_moment <= moment();

        function has_work_today(tid) {
            return any(cpt, function(val) {
                return val == tid;
            });
        }

        if (!lesson_canceled && happen && has_work_today(teacher.id)) {
            if(teacher.assistant) {
                return assist_sal;
            } else {
                var assists = $.grep($scope.data.teachers.list, function(t) {
                    return has_work_today(t.id) && t.assistant;
                });
                var sal = ($scope.calcTotal(index) - assist_sal * assists.length) / (cpt.length - assists.length);
                return sal;
            }
        } else {
            return null;
        }
    };

    $scope.totals = {
        calcTotal: function() {
            try {
                return $scope.data.dates.reduce(function(sum, cv, index) {
                    var total = $scope.calcLesson(index);
                    return sum + (total || 0)
                }, 0);
            } catch(e) {
                return 0;
            }
        },

        calcDanceHall: function() {
            try {
                var noCanceled = $scope.data.dates.filter(function(e) {
                    return !e.canceled;
                });
                return $scope.data.group.dance_hall.prise * noCanceled.length;
            } catch(e) {
                return 0;
            }
        },

        calcClubTax: function() {
            var sum = (this.calcTotal() - this.calcDanceHall()) * 0.3;
            return sum > 0 ? sum : 0;
        },

        calcProfit: function() {
            var sum = this.calcTotal() - this.calcDanceHall() - this.calcClubTax();
            return sum;
        },

        calcTeacherSalary: function(teacher) {
            try {
                return $scope.data.dates.reduce(function(sum, cv, index) {
                    var total = parseFloat($scope.calcTeacherSalary(teacher, index));
                    return sum + (total || 0)
                }, 0);
            } catch(e) {
                return 0;
            }
        },

        calcNextMonth: function() {
            try {
                var next_month_sum = $scope.data.out_of_range_lessons.reduce(function(total, lesson) {
                    return total + lesson.group_pass.pass_type.prise / lesson.group_pass.pass_type.lessons;
                }, 0);

                return next_month_sum;
            } catch(e) {
                return 0;
            }
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

        this.opened = false;
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
                org: false,
                is_new: true
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
        this.opened = true;
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
        $('.student-edit-widget').on('keypress', $.proxy(function(event) {
            if(event.originalEvent.code == "Enter") {
                this.save();
            }
        }, this));
    }

    StudentEditWidget.prototype.clear = function() {
        this.opened = false;
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
        $('.student-edit-widget').off('keypress');
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
                    // костыльььь
                    response.data.info.is_new = true;
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

    StudentEditWidget.prototype.delete = function(index, arr) {
        var self = this;

        if(!confirm("Подтвердите удаление ученика из группы")) {
            return;
        }

        $http({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            method: "POST",
            url: "/delete_student",
            data: {
                group: $scope.data.group.id,
                stid: arr[index].info.id
            }
        }).then(function() {
            self.remove(index, arr);
        }, function() {

        });
    }

    StudentEditWidget.prototype.trash = function(index) {
        alert("Method doesn't implemented");
    }
    
    $scope.studentEditWidget = new StudentEditWidget();


    GroupMovingWidget = function() {
        this.elem = $("#groupMoving").modal({
            show: false
        });
        
        $scope.$watch('$root.groups', $.proxy(function() {
            res = [];
            for(var i in $rootScope.groups) {
                res = res.concat($rootScope.groups[parseInt(i)].groups)
            }
            this.all_groups = res;
        }, this))
    }

    GroupMovingWidget.prototype.open = function(student) {
        this.student = student;  
        this.elem.modal("show");
    }

    GroupMovingWidget.prototype.save = function(date, new_group) {
        var data = {
            stid: this.student.info.id,
            new_group: parseInt(new_group),
            old_group: $scope.data.group.id,
            date: date
        }

        var self = this;

        $http({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            method: "POST",
            data: data,
            url: "/change_group"
        }).then(
            function() {
                load();
                self.close();
            }, function() {
            }
        );
    }

    GroupMovingWidget.prototype.close = function() {
        this.elem.modal("hide");
    }

    $scope.groupMoving = new GroupMovingWidget();

    var EditLessonWidget = function($elem) {
        this.elem = $($elem).modal({
            show: false
        });

        this.vacant_cnt = 0;
        this.vacant_group_pass = null;
        this.vacant_group_pass_color = "#fff";
        this.data = [];
    }

    EditLessonWidget.prototype.load = function(index) {
        var data = {
                group_id: $scope.data.group.id,
                from_date: $scope.data.selected_month,
                month_cnt: 3,
                student_id: $scope.main_list[index].info.id
            },
            self = this;

        $http({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            method: "POST",
            data: data,
            url: "/get_group_calendar"
        }).then(
            function(responce) {
                self.data = [];

                var data = responce.data,
                    days, gp_id, color, status, mth;
                
                for(var i=0, j=data.length; i<j; i++) {
                    mth = data[i];
                    days = mth.days.map(function(d) {
                        var gp_id = null,
                            color = '#fff',
                            status = 'vacant';

                        if('group_pass' in d.lesson_data) {
                            gp_id = d.lesson_data.group_pass.id;
                            
                            switch(d.lesson_data.status) {
                                case 0:
                                    status='occupied';
                                    break

                                case 1:
                                case 2:
                                case 4:
                                    status='locked';
                                    break

                                case -2:
                                    status='vacant';
                                    break
                            }

                            color = d.lesson_data.group_pass.color;
                        }

                        return {
                            day: moment(d.day, "DDMMYYYY"),
                            old_day: moment(d.day, "DDMMYYYY"),
                            group_pass: gp_id,
                            status: status,
                            old_status: status,
                            color: color 
                        } 
                    });

                    self.data.push({
                        month: month[mth.month],
                        days: days
                    });
                }

            }, function() {
            }
        )
    }

    EditLessonWidget.prototype.open = function(header, alert_msg, index, save_func) {

        this.vacant_group_pass = null;
        this.load(index)
        var dates = $scope.data.dates,
            lessons = $scope.main_list[index].lessons;
        this.student = $scope.main_list[index].info.last_name + " " + $scope.main_list[index].info.first_name;
        this.student_id = $scope.main_list[index].info.id;
        this.old_days = [];

        this.elem.modal("show"); 
        this.vacant_cnt = 0;

        this.header = header;
    }

    EditLessonWidget.prototype.close = function() {
        this.elem.modal("hide");
        this.data = [];
    }

    EditLessonWidget.prototype.save = function() {
        throw("Method not implemented");
    }

    EditLessonWidget.prototype.click = function(object, force) {
        if(object.status == 'vacant' && this.vacant_cnt == 0) {
            return;
        }
        if(!force && object.status == 'locked') {
            alert(this.lock_alert_msg);
            return;
        }

        if(force && object.status == 'locked') {
            object.status = "occupied";
        }

        var new_statuses = {
            vacant: "occupied",
            occupied: "vacant"
        };
        
        switch(object.status) {
            case "occupied":
                this.vacant_cnt++;
                this.vacant_group_pass = object.group_pass;
                this.vacant_group_pass_color = object.color;
                this.old_days.push(object.old_day);
                object.group_pass = null;
                object.color = "#fff";
                break

            case "vacant":
                this.vacant_cnt--;
                object.group_pass = this.vacant_group_pass;
                object.color = this.vacant_group_pass_color;
                object.old_day = this.old_days.pop();
                break
        }
        object.status = new_statuses[object.status];
    }

    $scope.moveLessonWidget = new EditLessonWidget("#moveLesson");

    $scope.moveLessonWidget.save = $.proxy(function() {
            if(!confirm("Будет выполненн перенос занятий. Продолжить?")) {
                return;
            }

            var data = {
                lessons: []
            };

            for(var i=0, j=this.data.length; i<j; i++) {
                var l = this.data[i].days;
                var nl = l.filter(function(e) {
                    return e.status == 'occupied';
                }).map(function(e) {
                    return {
                        gpid: e.group_pass,
                        old_date: e.old_day.format("DDMMYYYY"),
                        new_date: e.day.format("DDMMYYYY")
                    }
                }).filter(function(e) {
                    return e.old_date !== e.new_date;
                });

                data.lessons = data.lessons.concat(nl);
            }
            
            if(data.lessons.length != 0) {
                $http({
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    method: "POST",
                    data: data,
                    url: "/move_lessons"
                }).then($.proxy(function(responce) {
                    this.close();
                    load();
                }, this), 
                    $.proxy(function() {
                    alert("Ошибка при выполнении пененоса");
                    this.close();
                }, this))        
            } else {
                this.close();
            }
        },
        $scope.editLessonWidget
    )

    $scope.deleteLessonWidget = new EditLessonWidget("#deleteLesson");

    $scope.deleteLessonWidget.save = $.proxy(function() {
        res = [];
        
        for(var i=0, j=this.data.length; i<j; i++) {
            mth = this.data[i];
            dates = mth.days.filter(function(e) {
                return e.status == 'vacant' && e.old_status != 'vacant'
            }).map(function(e) {
                return e.day.format('DD.MM.YYYY');
            });

            res = res.concat(dates);
        }

        var data = {
            dates: res,
            group: $scope.data.group.id,
            stid: this.student_id
        }

        if(!confirm("Подтвердите удаление занятий")) {
            return;
        }

        $http({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            method: "POST",
            data: data,
            url: "delete_lessons"
        }).then(function(responce) {
            load();
        }, function() {})

        this.close();

    }, $scope.editLessonWidget);

    $scope.hideSidebar = function() {
        $rootScope.showSideBar = false;
    }

    //$timeout($scope.showSidebar, 100);
    
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

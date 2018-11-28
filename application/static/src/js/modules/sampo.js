// module
app.controller('sampoCtrl', function($scope, $timeout, $location, $interval, $http, $rootScope) {

    function sendRequest() {
        $http({
            method: "POST",
            url: "get_sampo_day",
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: JSON.stringify({
                date: $scope.selectedDate,
                hall: $scope.selectedDanceHall
            })
        }).then(function(data) {
            data = data.data;

            for(var i=0, j=data.payments.length; i<j; i++) {
                payment = data.payments[i]
                var time = moment(payment[0], 'DD.MM.YYYY HH:mm:SS').format('HH:mm');
                var amount = parseInt(payment[1]);

                if (amount > 0) {
                    fillPayments(time, amount);
                } else {
                    reason = payment[2]
                    fillWithdrawals(time, amount, reason);
                }
            }

            for(var i=0, j=data.passes.length; i<j; i++) {
                var pass = data.passes[i],
                    name = pass[0],
                    checked = pass[1],
                    pid = pass[2];
                fillPasses(name, checked, pid);
            }

            updateReport();
        });
    }

    function updateReport() {
        $http({
            method: "POST",
            url: "get_sampo_month",
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(function(response) {
            var data = response.data;
            $scope.report = response.data;
        });
    }
    
    var params = $location.search() 
    $scope.selectedMenu = null; 

    if (params['date'] !== undefined) {
        $scope.selectedDate = moment(params['date'], "DDMMYYYY");
        $scope.today = $scope.selectedDate.toDate().toString();
    } else {
        $scope.selectedDate = new Date();
        $scope.today = $scope.selectedDate.toString();
    }
    
    $scope.selectedDanceHall = params['hall'] || 4;

    $scope.selectMenu = function(elem) {
        $('.sampo-menu').css('background-color', 'inherit');
        $('.' + elem).css('background-color', '#007bff');
        
        this.selectedMenu = elem;
    }

    $scope.inAddProc = false;
    $scope.addRecord = function(action) {
        if(action == 'sampo-menu-add') {
            this.inAddProc = true;
        } else if (action == 'sampo-menu-writeoff') {
            this.inAddProc = true;
        }
    }

    function reset() {
        $scope.payments = [];
        $scope.withdrawals = [];
        $scope.passes = []; 
    }

    function fillPayments(time, amount) {
        $scope.payments.push({
            time: time,
            amount: amount
        });
    }

    function fillWithdrawals(time, amount, reason) {
        $scope.withdrawals.push({
            time: time,
            amount: amount,
            reason: reason
        });
    }

    function fillPasses(name, checked, pid) {
        $scope.passes.push({
            name: name,
            checked: checked,
            pid: pid
        });
    }

    // Добавление оплаты
    $scope.addPayment = function(time, amount) {
        var data = {
            date: this.selectedDate,
            time: time,
            amount: parseInt(amount),
            hall: this.selectedDanceHall
        };
        
        $http({
            method: "POST",
            url: "add_sampo_payment",
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: JSON.stringify(data)
        }).then(function(data) {
            fillPayments(time, amount);
        });
    }
    
    // Добавление списания
    $scope.addWriteoff = function(time, amount, reason) {
        amount = -1*amount
        var data = {
            date: this.selectedDate,
            time: time,
            amount: parseInt(amount),
            comment: reason,
            hall: this.selectedDanceHall
        };

        $http({
            method: "POST",
            url: "add_sampo_payment",
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: JSON.stringify(data)
        }).then(function(data) {
            fillWithdrawals(time, amount, reason);
        });
    }

    // Добавление абонементов
    $scope.addPass = function(time, amount, name) {
        var data = {
            date: this.selectedDate,
            time: time,
            amount: parseInt(amount),
            name: name,
            hall: this.selectedDanceHall
        };
        
        $http({
            method: "POST",
            url: "add_sampo_pass",
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: JSON.stringify(data)
        }).then(function(data) {
            fillPayments(time, amount);
            fillPasses(name, true, null);
        });
    }

    $scope.selectMenu('sampo-menu-add');
    
    // Обработчик изменения даты
    $scope.changeDate = function(newDate) {
        reset();
        sendRequest();
        var dt = newDate.replace(/\./g, '')
        $location.search('date', dt);
    };
    
    // Обработчик изменения зала
    $scope.changeHall = function(newHall) {
        reset();
        sendRequest();
        var dt = $scope.selectedDate.replace(/\./g, '')
        $location.search('hall', $scope.selectedDanceHall);
    };
    
    var lastChangeTime = null;

    $interval(function() {

        var now = moment(), 
            selectedDay = moment($scope.today).format('DD.MM.YYYY');

        if((moment() - lastChangeTime < 15000) || $scope.selectedDate != now.format('DD.MM.YYYY')) {
            return;
        }
        
        if((now.format("HH:mm")!= $scope.time)) {
            $scope.time = now.format("HH:mm");
        }

    }, 1000);
    
    var promice;
    $scope.manualTimeChange = function() {        
        lastChangeTime = moment();
        $timeout.cancel(promice);
        promice = $timeout(function() {
            var t = "" + $scope.time,
                hh, mm;

            t = t.replace(':', '');
            hh = parseInt(t.slice(0, 2));
            mm = parseInt(t.slice(2, 4));

            hh = hh > 23 ? 23 : hh;
            mm = mm > 59 ? 59 : mm;

            hh = ("0" + hh).slice(-2);
            mm = ("0" + mm).slice(-2);

            if(t.length > 2) {
                $scope.time = hh + ":" + mm;
            }
        }, 300);
    }

    $scope.checkSampo = function(pass) {
        pass.checked = !pass.checked;
        $http({
            method: "POST",
            url: "check_sampo_pass",
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: JSON.stringify({
                date: $scope.selectedDate,
                hall: $scope.selectedDanceHall,
                pid: pass.pid,
                val: pass.checked
            })
        }).then(function(data) {
        })
        
    }

    reset();
})

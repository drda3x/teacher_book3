// module
app.controller('sampoCtrl', function($scope, $timeout, $interval, $http) {

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
            data = data.data.payments;

            for(var i=0, j=data.length; i<j; i++) {
                var time = moment(data[i][0], 'DD.MM.YYYY HH:mm:SS').format('HH:mm');
                var amount = data[i][1];
                fillPayments(time, amount);
            }
        });
    }

    $scope.selectedMenu = null; 
    $scope.today = new Date();

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
        $scope.withdrawals.push({
            time: time,
            amount: amount,
            reason: reason
        });
    }
    
    // Добавление абонементов
    $scope.addPass = function(time, amount, name) {
        $scope.payments.push({
            time: time,
            amount: amount
        });

        $scope.passes.push({
            name: name,
            checked: true
        });
    }

    $scope.selectMenu('sampo-menu-add');
    
    // Обработчик изменения даты
    $scope.changeDate = function(newDate) {
        reset();
        sendRequest();
    };
    
    // Обработчик изменения зала
    $scope.changeHall = function(newHall) {
        reset();
        sendRequest();
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

    reset();
})

// module
app.controller('sampoCtrl', function($scope) {
    $scope.selectedMenu = null; 
    $scope.today = new Date().toString();

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

    $scope.payments = [];
    // Добавление оплаты
    $scope.addPayment = function(time, amount) {
        this.payments.push({
            time: time,
            amount: amount
        })
    }
    
    $scope.withdrawals = [];
    // Добавление списания
    $scope.addWriteoff = function(time, amount, reason) {
        $scope.withdrawals.push({
            time: time,
            amount: amount,
            reason: reason
        });
    }
    
    $scope.passes = []; 
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
})

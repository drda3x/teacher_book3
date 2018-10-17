// module
app.controller('sampoCtrl', function($scope) {
    $scope.selectedMenu = null; 

    $scope.selectMenu = function(elem) {
        $('.sampo-menu').css('background-color', 'inherit');
        $('.' + elem).css('background-color', '#007bff');
        
        this.selectedMenu = elem;
    }

    $scope.selectMenu('sampo-menu-add');
})

app.controller('navBarCtrl', function($scope, $rootScope) {
    $scope.header = null;
    $scope.header2 = null;

    $scope.$watch('$root.header', function() {
        $scope.header = $rootScope.header;
    });

    $scope.$watch('$root.header2', function() {
        $scope.header2 = $rootScope.header2;
    })
});

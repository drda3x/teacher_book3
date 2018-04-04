app.controller('sideBarCtrl', function($scope, $http, $location, $rootScope, $timeout) {
    $scope.elements = [];
    $scope.active = null;

    function checkUrl() {
        var path = $location.path().split('/'),
            category = path[1],
            id = parseInt(path[2]);
        
        $scope.active = id;
        $scope.showSideBar = category === '';
    }

    $scope.load = function() {
        $http({
            method: "GET",
            url: "/groups"
        }).then(function(response) {
            $scope.elements = response.data;
            $rootScope.groups = $scope.elements;
        }, function(response) {
            if(response.status == 403) {
                $location.path('/login')
            }
        })
    }

    $scope.$on('$locationChangeSuccess', checkUrl);

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

    $timeout(function() {
        checkUrl();
    }, 100)
});

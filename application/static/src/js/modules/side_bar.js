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
            $rootScope.groups = $scope.elements;
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

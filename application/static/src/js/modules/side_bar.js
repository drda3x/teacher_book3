app.controller('sideBarCtrl', function($scope, $http, $location, $rootScope) {
    $scope.groups = [];
    $scope.active = null;
    $scope.showSideBar = true;

    $scope.load = function() {
        $http({
            method: "GET",
            url: "/groups"
        }).then(function(response) {
            $scope.groups = response.data;
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

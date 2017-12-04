
app.controller('authCtrl', function($scope, $http, $location, $window, $rootScope) {
    $rootScope.showSideBar = false;
    $scope.login = function(uname, passwd) {
        $http({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            method: "POST",
            url: "/login",
            data: {
                username: uname,
                password: passwd
            }
        }).then(function(response) {
            $location.path('/');
            $rootScope.showSideBar = true;
        }, function(response) {
            console.log("ERROR")
        }); 
    };

    $scope.logout = function() {
        $http({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            method: "POST",
            url: "/logout"
        }).then(function(response) {
            $rootScope.showSideBar = false;
            $location.path('/login');
        }, function(response) {
        });
    }


});

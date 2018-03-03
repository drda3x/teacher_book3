
// Контроллер для страницы просмотра изменений в системе
app.controller("changeLogCtrl", function($scope, $http){
    $scope.changes = [];

    $http({
        method: "GET",
        url: '/view_changes',
    }).then(function(response) {
        $scope.changes = response.data;
    }, function(response) {
    });
})

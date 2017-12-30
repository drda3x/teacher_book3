
// Директива для задания динамического
// размера input'ов
app.directive('ngSize', function(){
    return {
        restrict: 'A',
        scope: {
            size: "=ngSize",
            defaultSize: '=defaultSize'
        },
        link: function(scope, element, attrs){
            if(!element.nodeName === 'SELECT'){
                return;
            }

            scope.$watch("size", function(val) {
                attrs.$set('size', val || scope.defaultSize);	
            })
        }
    }
});


app.directive('appComment', ["$timeout", "$http", function($timeout, $http) {
    return {
        restrict: 'E',
        scope: {
            group: "=",
            student: "=",
            disabled: "=disabled",
            value: "@"
        },
        template: '<textarea rows="2" cols="50" ' + 
                  'style="border: none; resize: none; background-color: inherit;" '+
                  'placeholder="{{placeholder}}"'+
                  'ng-disabled="disabled"'+
                  'ng-model="value"' + 
                  ' ></textarea>',
        replace: true,
        link: function(scope, elem, attrs) {
        },

        controller: function($scope, $element) {
            
            function sendRequest() {
                $http({
                    method: "POST",
                    url: '/edit_comment',
                    data: {
                        group: $scope.group,
                        student: $scope.student,
                        text: $scope.value
                    },
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
            }

            $scope.$watch('disabled', function(val) {
                if(!val) {
                    $('body').one('click', function(event) {
                        event.stopPropagation();
                        event.preventDefault();

                        $scope.$apply(function() {
                            $scope.disabled = true;
                        });

                        sendRequest();
                    });

                    $element.bind('click', function(event) {
                        event.stopPropagation();
                        event.preventDefault();
                    });

                    $timeout(function() {
                        $scope.placeholder = "Введите коментарий"
                        $element[0].focus();
                    });
                } else {
                    $scope.placeholder = ""
                }
            });
        }
    }
}]);

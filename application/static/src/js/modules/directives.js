
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
            text: "@",
            time: "@"
        },
        template: '<div>' + 
                  '<span ng-show="showTime()" class="bg-info text-white" '+
                    'style="font-size: 10pt; font-weight: bold; padding: 0 3px; border-radius: 5px">'+
                    '{{time}}'+
                  '</span>'+
                  '<textarea rows="{{rows}}" cols="50" ' + 
                  'style="border: none; resize: none; background-color: inherit;" '+
                  'placeholder="{{placeholder}}"'+
                  'ng-disabled="disabled"'+
                  'ng-model="text"' + 
                  ' ></textarea>' +
                  '</div>',
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
                        text: $scope.text
                    },
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                }).then(
                    function(response) {
                        $scope.time = response.data.time;
                        getRowsSize();
                    },
                    function() {}
                )
            }

            function getRowsSize() {
                $scope.rows = $scope.text.length > 40 ? 2 : 1;
            }

            $scope.$watch('disabled', function(val) {
                if(!val) {
                     var metaKeyState = false;

                    // Как по другому вызвать сохранение и сброс события клика - не знаю((
                    $element.bind('keydown', function(event) {
                        console.log(event);
                        if(event.key == "Enter") {
                            if(!(event.shiftKey || metaKeyState)) {
                                $('body').trigger('click');
                            }
                        } else if(event.keyCode == 91) {
                            metaKeyState = true;
                        }
                    });

                    $element.bind('keyup', function(event) {
                        if(event.keyCode == 91) {
                            metaKeyState = false;
                        }
                    });

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
                    $element.off('keydown');
                    $element.off('keyup');
                }
            });
          
            $scope.showTime = function() {
                return $scope.time != '' && $scope.time != undefined && $scope.text != '' && $scope.text != undefined;
            }
            
            $timeout(getRowsSize, 500);
        }
    }
}]);

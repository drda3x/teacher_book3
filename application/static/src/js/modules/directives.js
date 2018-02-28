
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


app.directive('appComment', ["$timeout", "$http", "$window", function($timeout, $http, $window) {
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
                  '<span ng-show="showTime() && !edit_text" class="bg-info text-white" '+
                    'style="font-size: 10pt; font-weight: bold; padding: 0 3px; border-radius: 5px; display: block; max-width: 111px">'+
                    '{{time}}'+
                  '</span>'+
                  '<textarea rows="1" cols="50" ' + 
                  'style="border: none; resize: none; background-color: inherit; overflow: hidden" '+
                  'placeholder="{{placeholder}}"'+
                  'ng-show="edit_text"' +
                  'ng-model="raw_text"' + 
                  ' ></textarea>' +
                  '<div class="text" ng-hide="edit_text" ng-dblclick="goEdit()" style="max-height: 23px; max-width:95%; margin-bottom: -5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">'+
                      '<span>{{text}}</span>' +
                  '</div>' +
                  '<div style="display: inline-block" ng-show="display_short">...</div>' +
                  '</div>',
        replace: true,
        link: function(scope, elem, attrs) {
        },

        controller: function($scope, $element, $window) {
            $scope.edit_text = false;
            
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
                        hideExcess();
                    },
                    function() {}
                )
            }

            function hideExcess() {
                var w = angular.element($element[0])[0]
                $scope.display_short = $scope.text.length * 8 > w.offsetWidth; 
                $scope.display_short = false;
            }

            $scope.goEdit = function() {
                $scope.edit_text = true;
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
                        $scope.edit_text = false;
                    });

                    sendRequest();
                    $element.off('keydown');
                    $element.off('keyup');

                });

                $element.bind('click', function(event) {
                    event.stopPropagation();
                    event.preventDefault();
                });
            }

            $scope.$watch('edit_text', function(val) {
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
                            $scope.edit_text = false;
                        });

                        sendRequest();
                    });

                    $element.bind('click', function(event) {
                        event.stopPropagation();
                        event.preventDefault();
                    });

                    /*
                    $timeout(function() {
                        $scope.placeholder = "Введите коментарий"
                        $element[0].focus();
                    });
                    */
                } else {
                    $scope.placeholder = ""
                    $element.off('keydown');
                    $element.off('keyup');
                }
            });
          
            $scope.showTime = function() {
                return $scope.time != '' && $scope.time != undefined && $scope.text != '' && $scope.text != undefined;
            }
            
            $timeout(hideExcess, 200);
        }
    }
}]);

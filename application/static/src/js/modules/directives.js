
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


app.directive('appComment', function() {
    return {
        restrict: 'E',
        scope: {
            group: "@",
            student: "@",
            disabled: "=disabled"
        },
        template: '<textarea rows="2" cols="50" ' + 
                  'style="border: none; resize: none; background-color: inherit;" '+
                  'placeholder="Введите коментарий"'+
                  'ng-disabled="disabled"'+
                  ' ></textarea>',
        replace: true,
        link: function(scope, elem, attrs) {
        },

        controller: function($scope) {
            $scope.$watch('disabled', function(val) {
                if(!val) {
                    $('body').one('click', function(event) {
                        event.stopPropagation();
                        event.preventDefault();

                        $scope.$apply(function() {
                            $scope.disabled = true;
                        });
                    })
                }
            });
        }
    }
});

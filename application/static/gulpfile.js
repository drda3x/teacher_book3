'use strict';

var gulp = require("gulp");
var concat = require("gulp-concat");
var rigger = require("gulp-rigger");


gulp.task('vendor', function() {
    gulp.src([
        "bower_components/angular/angular.js",
        "bower_components/angular-route/angular-route.js",
        "bower_components/jquery/dist/jquery.js",
        "bower_components/bootstrap/dist/js/bootstrap.js",
        "bower_components/angularjs-datepicker/dist/angular-datepicker.js",
        "bower_components/alertifyjs/dist/js/alertify.js"
    ]).pipe(concat("vendor.js"))
        .pipe(gulp.dest("build"));
});


gulp.task('js', function() {
    gulp.src('src/js/vendor.js')
        .pipe(concat())
        .pipe(gulp.dest('build'));

    gulp.src('src/js/app.js')
        .pipe(rigger())
        .pipe(gulp.dest('build'));
});

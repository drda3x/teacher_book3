'use strict';

var gulp = require("gulp");
var concat = require("gulp-concat");
var rigger = require("gulp-rigger");
var concatCss = require("gulp-concat-css");


gulp.task('vendor:js', function() {
    gulp.src([
        "bower_components/angular/angular.js",
        "bower_components/angular-route/angular-route.js",
        "bower_components/jquery/dist/jquery.js",
        "node_modules/bootstrap/dist/js/bootstrap.bundle.js",
        "node_modules/moment/moment.js",
        "bower_components/angularjs-datepicker/dist/angular-datepicker.js",
        "bower_components/alertifyjs/src/js/alertify.js"
    ]).pipe(concat("vendor.js"))
        .pipe(gulp.dest("build"));
});


gulp.task("vendor:css", function() {
    gulp.src([
        "node_modules/bootstrap/dist/css/bootstrap.css",
        "bower_components/alertifyjs/dist/css/alertify.css",
        "bower_components/angularjs-datepicker/dist/angular-datepicker.css"
    ]) .pipe(concatCss("vendor.css"))
    .pipe(gulp.dest('build'));
});


gulp.task('js', function() {
    gulp.src('src/js/app.js')
        .pipe(rigger())
        .pipe(gulp.dest('build'));
});


gulp.task('watch', function() {
    gulp.watch('src/js/modules/*.js', ['js']);
});

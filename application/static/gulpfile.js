'use strict';

var gulp = require("gulp");
var concat = require("gulp-concat");
var bower = require("gulp-bower-files");
var gulpFilter = require("gulp-filter");
var rigger = require("gulp-rigger");


//
// concat *.js to `vendor.js`
// and *.css to `vendor.css`
// rename fonts to `fonts/*.*`
//
gulp.task('bower', function() {
  var jsFilter = gulpFilter('**/*.js')
  var cssFilter = gulpFilter('**/*.css')
  return bower()
    .pipe(jsFilter)
    .pipe(concat('vendor.js'))
    .pipe(gulp.dest('build'))
    //.pipe(jsFilter.restore())
    .pipe(cssFilter)
    .pipe(concat('vendor.css'))
    .pipe(gulp.dest('build'))
    //.pipe(cssFilter.restore())
    //.pipe(rename(function(path) {
    //  if (~path.dirname.indexOf('fonts')) {
    //    path.dirname = '/fonts'
    //  }
    //}))
    //.pipe(gulp.dest(dist.vendor))
});


gulp.task('js', function() {
    gulp.src('src/js/app.js')
        .pipe(rigger())
        .pipe(gulp.dest('build'))
});

'use strict';

var gulp = require("gulp");
var concat = require("gulp-concat");
var bower = require("gulp-bower-files");
var gulpFilter = require("gulp-filter");


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
    .pipe(gulp.dest('js'))
    //.pipe(jsFilter.restore())
    .pipe(cssFilter)
    .pipe(concat('vendor.css'))
    .pipe(gulp.dest('css'))
    //.pipe(cssFilter.restore())
    //.pipe(rename(function(path) {
    //  if (~path.dirname.indexOf('fonts')) {
    //    path.dirname = '/fonts'
    //  }
    //}))
    //.pipe(gulp.dest(dist.vendor))
})

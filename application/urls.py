"""route URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
import views
import rest_api


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^groups$', rest_api.get_list, name="groups"),
    url(r'^group/', rest_api.get_base_info),
    url(r'^login$', rest_api.login),
    url(r'^logout$', rest_api.logout),
    url(r'^edit_student', rest_api.edit_student),
    url(r'^process_lesson', rest_api.process_lesson),
    url(r'^delete_lessons', rest_api.delete_lessons),
    url(r'^move_lessons', rest_api.move_lessons),
    url(r'^cancel_lesson', rest_api.cancel_lesson),
    url(r'^restore_lesson', rest_api.restore_lesson),
    url(r'^delete_student', rest_api.delete_student),
    url(r'^$', views.index, name="index"),
]

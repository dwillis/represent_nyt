from django.conf.urls.defaults import *
from django.contrib.gis import admin
from projects.represent import views

admin.autodiscover()

handler404 = 'projects.represent.views.index'

urlpatterns = patterns('',

     (r'^represent/q/admin/overview$', views.admin_overview),
     (r'^represent/q/admin/(.*)', admin.site.root),
     (r'^represent/everyblock$', views.everyblock),
     (r'^represent/fortgreene$', views.fortgreene),
     (r'^represent/(?P<location>.+).xml$', views.results_feed),
     (r'^represent/(?P<location>.+)/onthefloor/$', views.onthefloor),
     (r'^represent/(?P<location>.+)/aroundtheweb/$', views.aroundtheweb),
     (r'^represent/(?P<location>.+)/activityfeed/$', views.activityfeed),
     (r'^represent/(?P<location>.+)/$', views.results),
     (r'^represent/logout$', views.logout),
     (r'^represent/$', views.index),
     (r'^represent/office/(?P<id>\d+)/district.kml$', views.district_kml),
     (r'^represent/office/(?P<id>\d+)/gmap/$', views.gmap),

)

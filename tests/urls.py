from __future__ import unicode_literals

# Django
from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

# Local Apps
from core.views import DummyView


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^for-reversing-in-templates/(?P<pk>[\d]+)/$', DummyView.as_view(), name="dummy-view"),
    url(r'^grapevine/', include('grapevine.urls', namespace='grapevine')),
]

urlpatterns += staticfiles_urlpatterns()
from __future__ import unicode_literals

# Django
from django.conf.urls import url

# Local Apps
from .views import ViewEmailOnSite


urlpatterns = [
    url(r"view/(?P<message_guid>.*)/$", ViewEmailOnSite.as_view(), name="view-on-site")
]
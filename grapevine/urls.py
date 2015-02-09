from __future__ import unicode_literals
import inspect

# Django
from django.conf.urls import include, url

# Local Apps
from .emails import backends

urlpatterns = []

for attr_name in dir(backends):
    attr = getattr(backends, attr_name)
    if inspect.isclass(attr) and issubclass(attr, backends.base.GrapevineEmailBackend):
        try:
            # TODO: Formally activate these.
            backend = attr()
            urlpatterns += backend.get_urls()
        except:
            pass


urlpatterns.append(url(r"^", include("grapevine.emails.urls")))

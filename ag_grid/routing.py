from django.conf import settings
from django.urls import include, re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/(?P<app_label>\w+)/(?P<model_name>\w+)/$", consumers.ModelConsumer.as_asgi()),
]

try:
    from ag_grid.contrib.notification.consumers import AgGridNotificationConsumer

    websocket_urlpatterns += [
        re_path(r"ws/notifications/$", AgGridNotificationConsumer.as_asgi()),
    ]
except ImportError:
    pass

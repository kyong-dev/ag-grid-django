from django.urls import path

from . import api

app_name = "ag_grid_notification"

urlpatterns = [
    path("", api.AgGridNotificationListAPIView.as_view(), name="list"),
    path("<int:pk>/mark-read/", api.AgGridNotificationMarkReadAPIView.as_view(), name="mark-read"),
    path("send-notification/", api.SendAgGridNotificationAPIView.as_view(), name="send"),
]

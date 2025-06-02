from django.urls import path

from . import api

app_name = "notification"

urlpatterns = [
    path("", api.NotificationListAPIView.as_view(), name="list"),
    path("<int:pk>/mark-read/", api.NotificationMarkReadAPIView.as_view(), name="mark-read"),
    path("send-notification/", api.SendNotificationAPIView.as_view(), name="send"),
]

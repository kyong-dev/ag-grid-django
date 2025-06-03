from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ag_grid.permissions import AgGridModelPermission

from .models import AgGridNotification
from .utils import send_notification

User = get_user_model()


class AgGridNotificationListAPIView(APIView):
    """API to get user's notifications"""

    # permission_classes = [AgGridModelPermission]
    @swagger_auto_schema(
        operation_description="Retrieve notifications for the current user",
        operation_summary="Get notifications for current user",
        responses={
            200: openapi.Response(
                description="List of notifications",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Notification ID"),
                            "type": openapi.Schema(type=openapi.TYPE_STRING, description="Notification type"),
                            "title": openapi.Schema(type=openapi.TYPE_STRING, description="Notification title"),
                            "message": openapi.Schema(type=openapi.TYPE_STRING, description="Notification message"),
                            "action_url": openapi.Schema(type=openapi.TYPE_STRING, description="Action URL (optional)"),
                            "file_url": openapi.Schema(type=openapi.TYPE_STRING, description="File URL (optional)"),
                            "is_read": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Read status"),
                            "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Creation timestamp"),
                        },
                    ),
                ),
            ),
            403: "Forbidden",
        },
        tags=[_("AgGrid Notifications")],
    )
    def get(self, request):
        """Get notifications for current user"""
        user = request.user

        limit = int(request.query_params.get("limit", 50))

        # Filter for user's notifications (personal + staff-wide)
        notifications = AgGridNotification.objects.filter(Q(user=user, target_type="specific_user") | Q(target_type="all_staff")).exclude(is_read=True).order_by("-created_at")[:limit]

        # Serialize for API response
        data = [
            {"id": n.id, "type": n.type, "title": n.title, "message": n.message, "action_url": n.action_url, "file_url": n.file_url, "is_read": n.is_read, "created_at": n.created_at.isoformat()}
            for n in notifications
        ]

        return Response(data)


class AgGridNotificationMarkReadAPIView(APIView):
    """API to mark notification as read"""

    # permission_classes = [AgGridModelPermission]
    @swagger_auto_schema(
        operation_description="Mark a notification as read",
        operation_summary="Mark notification as read",
        responses={
            200: openapi.Response(description="Notification marked as read successfully"),
            403: "Forbidden - You do not have permission to mark this notification as read",
            404: "Notification not found",
        },
        tags=[_("AgGrid Notifications")],
    )
    def post(self, request, pk):
        """Mark notification as read"""
        try:
            notification = AgGridNotification.objects.get(pk=pk)

            # Security: only allow marking if user has access to this notification
            if notification.target_type == "all_staff" or (notification.target_type == "specific_user" and notification.user == request.user):
                notification.mark_as_read()
                return Response({"success": True})

            return Response({"error": "You do not have permission to mark this notification as read"}, status=status.HTTP_403_FORBIDDEN)

        except AgGridNotification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)


class SendAgGridNotificationAPIView(APIView):
    """API to create and send a new notification"""

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Send a new notification",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "type": openapi.Schema(type=openapi.TYPE_STRING, description="Notification type", default="custom"),
                "target_type": openapi.Schema(type=openapi.TYPE_STRING, description="Target type", default="all_staff"),
                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="User ID for specific user targeting"),
                "title": openapi.Schema(type=openapi.TYPE_STRING, default="테스트 메세지", description="Notification title"),
                "message": openapi.Schema(type=openapi.TYPE_STRING, default="긴급: 카테고리로 이동", description="Notification message"),
                "action_url": openapi.Schema(type=openapi.TYPE_STRING, default="http://localhost:8002/admin/product/category/", description="URL for action button (optional)"),
                # "file_url": openapi.Schema(type=openapi.TYPE_STRING, description="File URL for attachments (optional)"),
            },
            required=["type", "title", "message"],
        ),
        responses={
            201: openapi.Response(
                description="Notification created successfully",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"id": openapi.Schema(type=openapi.TYPE_INTEGER), "message": openapi.Schema(type=openapi.TYPE_STRING)}),
            ),
            400: "Bad Request",
        },
        tags=[_("AgGrid Notifications")],
    )
    def post(self, request):
        """Create new notification"""
        data = request.data

        # Handle user targeting
        target_type = data.get("target_type", "all_staff")
        user = None

        if target_type == "specific_user":
            user_id = data.get("user_id")
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Create notification
        notification = AgGridNotification.objects.create(
            type=data.get("type", "custom"), target_type=target_type, user=user, title=data.get("title"), message=data.get("message"), action_url=data.get("action_url"), file_url=data.get("file_url")
        )

        # Send via WebSocket
        send_notification(notification)

        return Response({"id": notification.id, "message": "Notification sent successfully"}, status=status.HTTP_201_CREATED)

import json

from django.db.models import Q

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class AgGridNotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications

    Handles:
    - Initial connection authentication
    - Subscription to user-specific and staff-wide channels
    - Sending unread notifications on connect
    - Real-time notification delivery
    - Mark-as-read functionality
    """

    async def connect(self):
        """Authenticate connection and join notification groups"""
        print("Connection attempt to NotificationConsumer")
        self.user = self.scope["user"]

        # Only allow authenticated staff users
        if not self.user.is_authenticated or not self.user.is_staff:
            await self.close()
            return

        # Create channel groups: user-specific and all-staff
        self.user_group = f"user_{self.user.id}_notifications"
        self.staff_group = "all_staff_notifications"

        # Join channel groups
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.staff_group, self.channel_name)

        # Accept the connection
        await self.accept()

        # Send unread notifications on connect
        await self.send_unread_notifications()

    async def disconnect(self, close_code):
        """Leave notification groups on disconnect"""
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        await self.channel_layer.group_discard(self.staff_group, self.channel_name)

    async def receive(self, text_data):
        """Process incoming WebSocket messages"""
        try:
            print("Received data in NotificationConsumer:", text_data)
            data = json.loads(text_data)
            action = data.get("action")

            # Handle mark-as-read actions
            if action == "mark_read":
                notification_id = data.get("notification_id")
                success = await self.mark_notification_as_read(notification_id)

                # Confirm action to client
                await self.send(text_data=json.dumps({"type": "action_response", "action": "mark_read", "success": success, "notification_id": notification_id}))
        except json.JSONDecodeError:
            pass  # Ignore invalid JSON

    async def notification(self, event):
        """Relay notification to client"""
        await self.send(text_data=json.dumps({"type": "notification", "notification": event["notification"]}))

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Database operation to mark notification as read"""
        from .models import AgGridNotification

        try:
            notification = AgGridNotification.objects.get(id=notification_id)
            # Verify user has permission to mark this notification
            if notification.target_type == "all_staff" or notification.user_id == self.user.id:
                notification.mark_as_read()
                return True
            return False
        except AgGridNotification.DoesNotExist:
            return False

    @database_sync_to_async
    def get_unread_notifications(self):
        """Fetch unread notifications for this user"""
        from .models import AgGridNotification

        # Get both user-specific and all-staff notifications
        notifications = AgGridNotification.objects.filter(Q(user=self.user, target_type="specific_user") | Q(target_type="all_staff")).filter(is_read=False).order_by("-created_at")[:10]

        # Convert to serializable format
        return [{"id": n.id, "type": n.type, "title": n.title, "message": n.message, "action_url": n.action_url, "file_url": n.file_url, "created_at": n.created_at.isoformat()} for n in notifications]

    async def send_unread_notifications(self):
        """Send existing unread notifications to client"""
        notifications = await self.get_unread_notifications()
        if notifications:
            await self.send(text_data=json.dumps({"type": "unread_notifications", "notifications": notifications}))

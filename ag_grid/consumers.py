import json

from django.apps import apps
from django.utils import timezone

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

# Global state management (resets when server restarts)
connected_users = {}  # Model-specific connected users {room_name: {channel_id: user_info}}
recent_changes = {}  # Model-specific recent changes history {room_name: [change_logs]}


class ModelConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer that broadcasts model data changes in real-time
    Provides connections, change propagation, and connected user management for each model
    """

    async def connect(self):
        """Setup and initialize WebSocket connection"""
        # Extract app label and model name from URL
        self.app_label = self.scope["url_route"]["kwargs"]["app_label"]
        self.model_name = self.scope["url_route"]["kwargs"]["model_name"]

        # Set user information
        self.user = self.scope.get("user")
        self.user_id = str(self.user.id) if self.user and self.user.is_authenticated else None
        self.username = self.user.username if self.user and self.user.is_authenticated else None

        # Verify model exists
        try:
            model = apps.get_model(self.app_label, self.model_name)
        except LookupError:
            await self.close()
            return

        # Permission check (optional)
        if self.user and self.user.is_authenticated:
            has_permission = await self.check_permission(self.user, model)
            if not has_permission:
                await self.close()
                return

        # Create group name for the model (viewers of the same model belong to the same group)
        self.room_group_name = f"{self.app_label}_{self.model_name}"

        # Add to channel layer group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept WebSocket connection
        await self.accept()

        # Add to connected users list
        if self.room_group_name not in connected_users:
            connected_users[self.room_group_name] = {}

        connected_users[self.room_group_name][self.channel_name] = {"user_id": self.user_id, "username": self.username, "timestamp": timezone.now().isoformat()}

        # Send updated user list to all clients
        await self.send_connected_users()

        # Send recent change history (optional)
        if self.room_group_name in recent_changes:
            await self.send(text_data=json.dumps({"type": "change_logs", "logs": recent_changes[self.room_group_name]}))

    ## Hide rows functionality
    async def receive(self, text_data):
        """Process WebSocket messages received from clients"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            # Process row hiding messages
            if message_type == "hide_rows":
                rows = data.get("rows", [])

                # Send hide notification to all connected clients
                await self.channel_layer.group_send(self.room_group_name, {"type": "rows_hidden_notification", "rows": rows, "hidden_by": self.username or "anonymous"})
        except json.JSONDecodeError:
            pass  # Ignore invalid JSON

    ## Hide rows functionality
    async def rows_hidden_notification(self, event):
        """Send row hiding notification to clients"""
        await self.send(text_data=json.dumps({"type": "rows_hidden", "rows": event["rows"], "hidden_by": event["hidden_by"]}))

    async def disconnect(self, close_code):
        """Handle WebSocket connection termination"""
        # Remove from connected users list
        if self.room_group_name in connected_users and self.channel_name in connected_users[self.room_group_name]:
            del connected_users[self.room_group_name][self.channel_name]

            # Clean up group if no users remain
            if not connected_users[self.room_group_name]:
                del connected_users[self.room_group_name]

        # Remove from channel layer group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Send updated user list
        await self.send_connected_users()

    async def send_connected_users(self):
        """Send connected users list to all clients"""
        users_list = []
        if self.room_group_name in connected_users:
            users_list = list(connected_users[self.room_group_name].values())

        await self.channel_layer.group_send(self.room_group_name, {"type": "connected_users_update", "users": users_list})

    async def connected_users_update(self, event):
        """Send connected users list update message"""
        await self.send(text_data=json.dumps({"type": "connected_users", "users": event["users"]}))

    async def model_update(self, event):
        """Handle model data changes and notify clients

        Note: is_source flag is used to prevent duplicate logs
        """
        # Save change log (only if necessary fields exist)
        if event.get("is_source", False) and "data" in event:
            log_data = event["data"]

            # Initialize change history list for this model if needed
            if self.room_group_name not in recent_changes:
                recent_changes[self.room_group_name] = []

            # Add latest change at the beginning
            recent_changes[self.room_group_name].insert(0, log_data)

            # Keep only last 20 entries (memory management)
            if len(recent_changes[self.room_group_name]) > 20:
                recent_changes[self.room_group_name] = recent_changes[self.room_group_name][:20]

        # Send update to client
        await self.send(text_data=json.dumps({"type": "model_update", "data": event["data"]}))

    @database_sync_to_async
    def check_permission(self, user, model):
        """Check if user has permission to view the model"""
        perm_codename = f"view_{model._meta.model_name}"
        return user.has_perm(f"{model._meta.app_label}.{perm_codename}")

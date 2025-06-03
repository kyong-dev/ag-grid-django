from django.utils.encoding import force_str

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_notification_to_user(user_id, notification_data):
    """
    Send notification to a specific user

    Args:
        user_id: ID of the target user
        notification_data: Dictionary containing notification details
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(f"user_{user_id}_notifications", {"type": "notification", "notification": notification_data})


def send_notification_to_all_staff(notification_data):
    """
    Send notification to all staff users

    Args:
        notification_data: Dictionary containing notification details
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)("all_staff_notifications", {"type": "notification", "notification": notification_data})


def send_notification(notification):
    """
    Send notification object through WebSocket

    Args:
        notification: Notification model instance
    """
    # Convert notification to serializable format
    notification_data = {
        "id": notification.id,
        "type": force_str(notification.type),
        "title": force_str(notification.title),
        "message": force_str(notification.message),
        "action_url": force_str(notification.action_url) if notification.action_url else None,
        "file_url": force_str(notification.file_url) if notification.file_url else None,
        "created_at": notification.created_at.isoformat(),
    }

    # Send to appropriate targets
    if notification.target_type == "specific_user" and notification.user:
        send_notification_to_user(notification.user.id, notification_data)
    else:
        send_notification_to_all_staff(notification_data)

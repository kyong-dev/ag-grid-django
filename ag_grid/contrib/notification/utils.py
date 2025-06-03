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
    async_to_sync(channel_layer.group_send)(f"user_{user_id}_notifications", {"type": "notification", "notification": notification_data})


def send_notification_to_all_staff(notification_data):
    """
    Send notification to all staff users

    Args:
        notification_data: Dictionary containing notification details
    """
    channel_layer = get_channel_layer()
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


def send_model_notification(notification_data):
    """
    모델 업데이트를 WebSocket을 통해 알림으로 보냅니다.
    
    Args:
        notification_data (dict): 알림 데이터 (type, data, group 필드 포함)
    
    예시:
        send_model_notification({
            "type": "model_update",
            "data": {
                "id": "123",
                "field": "name",
                "value": "New Value",
                ...
            },
            "group": "app_label_model_name"
        })
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            print("Channel layer not available")
            return False
            
        group_name = notification_data.get("group")
        if not group_name:
            print("Group name not provided in notification data")
            return False
            
        message_type = notification_data.get("type", "model_update")
        message_data = notification_data.get("data", {})
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": message_type,
                "data": message_data
            }
        )
        return True
    except Exception as e:
        print(f"Error sending model notification: {e}")
        return False
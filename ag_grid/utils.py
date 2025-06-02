from django.apps import apps
from django.utils import timezone

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_model_change(app_label, model_name, instance_id, field, value, previous_value=None, user=None):
    """
    Send a real-time notification about a model change via WebSockets.

    Args:
        app_label (str): The app label of the model (e.g., 'product')
        model_name (str): The name of the model (e.g., 'Product')
        instance_id (int/str): The ID of the changed instance
        field (str): The name of the changed field
        value: The new value
        previous_value: The previous value (optional)
        user: The user who made the change (optional)

    Returns:
        bool: True if notification was sent, False otherwise
    """
    try:
        # Get the channel layer
        channel_layer = get_channel_layer()
        if not channel_layer:
            return False

        # Create the group name in the same format as the consumer
        room_group_name = f"{app_label}_{model_name}"

        # Try to get the field's verbose name
        field_display = field
        try:
            model = apps.get_model(app_label, model_name)
            field_obj = model._meta.get_field(field)
            field_display = str(getattr(field_obj, "verbose_name", field))
        except (LookupError, AttributeError):
            pass

        # Prepare user information
        user_id = None
        username = "System"
        # if user:
        #     user_id = user.id if hasattr(user, 'id') else None
        #     username = user.username if hasattr(user, 'username') else "Unknown User"

        # Broadcast the update
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "model_update",
                "is_source": True,
                "data": {
                    "id": str(instance_id),
                    "field": field,
                    "field_display": field_display,
                    "value": value,
                    "previousValue": previous_value,
                    "user_id": user_id,
                    "username": username,
                    "timestamp": timezone.now().isoformat(),
                    "app_label": app_label,
                    "model_name": model_name,
                },
            },
        )
        return True
    except Exception as e:
        print(f"Error sending WebSocket notification: {e}")
        return False


def notify_bulk_changes(app_label, model_name, changes, user=None):
    """
    Send multiple change notifications at once.

    Args:
        app_label (str): The app label of the model
        model_name (str): The name of the model
        changes (list): List of dictionaries with keys:
                       'id', 'field', 'value', 'previous_value' (optional)
        user: The user who made the changes (optional)

    Returns:
        int: Number of successful notifications
    """
    successful = 0
    for change in changes:
        if "id" in change and "field" in change and "value" in change:
            previous = change.get("previous_value", None)
            if notify_model_change(app_label, model_name, change["id"], change["field"], change["value"], previous, user):
                successful += 1

    return successful

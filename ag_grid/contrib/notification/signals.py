from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AgGridNotification
from .utils import send_notification

# Optional: Set up signal to monitor product inventory levels
if "product" in settings.INSTALLED_APPS:

    @receiver(post_save, sender="product.Product")
    def check_product_stock_level(sender, instance, created, **kwargs):
        """Monitor product stock levels and send notifications when low"""
        # Check if we need to send a low stock notification
        if not hasattr(instance, "minimum_stock") or instance.minimum_stock is None:
            return

        send_notification = False

        # For new products
        if created and instance.quantity <= instance.minimum_stock:
            send_notification = True

        # For updated products
        elif not created and hasattr(instance, "_previous_quantity"):
            if instance._previous_quantity > instance.minimum_stock and instance.quantity <= instance.minimum_stock:
                send_notification = True

        if send_notification:
            notification = AgGridNotification.create_low_stock_notification(instance)
            send_notification(notification)

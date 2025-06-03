from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AgGridNotification(models.Model):
    """
    Store notification data for admin users

    Notifications can be targeted to specific users or all staff,
    and include metadata for different notification types and actions.
    """

    NOTIFICATION_TYPES = (
        ("export_complete", _("Excel Export Complete")),
        ("low_stock", _("Low Stock Alert")),
        ("system", _("System Notification")),
        ("custom", _("Custom Notification")),
    )

    TARGETS = (
        ("all_staff", _("All Staff")),
        ("specific_user", _("Specific User")),
    )

    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, verbose_name=_("Notification Type"))
    target_type = models.CharField(max_length=50, choices=TARGETS, default="all_staff", verbose_name=_("Target Type"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications", verbose_name=_("Target User"))
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    message = models.TextField(verbose_name=_("Message"))
    action_url = models.URLField(max_length=255, null=True, blank=True, verbose_name=_("Action URL"))
    file_url = models.URLField(max_length=255, null=True, blank=True, verbose_name=_("File URL"))
    is_read = models.BooleanField(default=False, verbose_name=_("Read Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ["-created_at"]
        db_table = "ag_grid_notification"
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["target_type"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])

    @classmethod
    def create_export_notification(cls, user, filename, file_url):
        """Factory method for creating export notifications"""
        return cls.objects.create(
            type="export_complete",
            target_type="specific_user" if user else "all_staff",
            user=user,
            title=_("Excel Export Complete"),
            message=_('File "{}" has been successfully exported.').format(filename),
            action_url=file_url,
            file_url=file_url,
        )

    @classmethod
    def create_low_stock_notification(cls, product):
        """Factory method for creating low stock notifications"""
        return cls.objects.create(
            type="low_stock",
            target_type="all_staff",
            title=_("Low Stock Alert"),
            message=_('Product "{}" has fallen below minimum stock level ({}/{}).').format(product.name, product.quantity, product.minimum_stock),
            action_url=f"/admin/product/product/{product.id}/change/",
        )

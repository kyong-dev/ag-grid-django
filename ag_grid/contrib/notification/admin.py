from django.contrib import admin

from .models import AgGridNotification


@admin.register(AgGridNotification)
class AgGridNotificationAdmin(admin.ModelAdmin):
    """Admin interface for notifications"""

    list_display = ("title", "type", "target_type", "user", "is_read", "created_at")
    list_filter = ("type", "target_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username")
    readonly_fields = ("created_at",)
    actions = ["mark_as_read"]

    def mark_as_read(self, request, queryset):
        """Admin action to mark notifications as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notifications marked as read.")

    mark_as_read.short_description = "Mark selected notifications as read"

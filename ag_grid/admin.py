from django.contrib import admin
from django.utils.html import format_html

from ag_grid.log import GridEditLog


@admin.register(GridEditLog)
class GridEditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "action", "model", "object_id", "field", "display_values", "user"]
    list_filter = ["timestamp", "action", "model", "user"]
    search_fields = ["model", "object_id", "field", "old_value", "new_value", "user__username"]
    readonly_fields = ["timestamp", "action", "model", "object_id", "field", "old_value", "new_value", "user", "object_data"]
    date_hierarchy = "timestamp"

    def display_values(self, obj):
        if obj.action == "CREATE":
            return format_html('<span style="color: #00cc00;">Created</span>')
        elif obj.action == "DELETE":
            return format_html('<span style="color: #cc0000;">Deleted</span>')
        else:
            return format_html('<span style="color: #cc0000; text-decoration: line-through;">{}</span> → <span style="color: #00cc00;">{}</span>', obj.old_value or "", obj.new_value or "")

    display_values.short_description = "Value Change"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

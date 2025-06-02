from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class GridEditLog(models.Model):
    ACTION_CHOICES = (
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("ACTION", "Action"),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default="UPDATE")
    model = models.CharField(max_length=100)
    object_id = models.CharField(null=True, max_length=100)
    field = models.CharField(max_length=100, blank=True)  # May be blank for CREATE/DELETE operations
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    # For storing full object data (useful for CREATE/DELETE operations)
    object_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "grid_edit_log"
        verbose_name = "Grid Edit Log"
        verbose_name_plural = "Grid Edit Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        if self.action == "CREATE":
            return f"Created {self.model} {self.object_id} by {self.user if self.user else 'System'} on {self.timestamp}"
        elif self.action == "DELETE":
            return f"Deleted {self.model} {self.object_id} by {self.user if self.user else 'System'} on {self.timestamp}"
        else:  # UPDATE
            return f"Updated {self.model} {self.object_id} - {self.field} [{self.old_value} -> {self.new_value}] by {self.user if self.user else 'System'} on {self.timestamp}"

    # Helper class methods for easy logging
    @classmethod
    def log_create(cls, model_name, object_id, user=None, object_data=None):
        return cls.objects.create(action="CREATE", model=model_name, object_id=object_id, user=user, object_data=object_data)

    @classmethod
    def log_update(cls, model_name, object_id, field, old_value, new_value, user=None):
        return cls.objects.create(action="UPDATE", model=model_name, object_id=object_id, field=field, old_value=old_value, new_value=new_value, user=user)

    @classmethod
    def log_delete(cls, model_name, object_id, user=None, object_data=None):
        return cls.objects.create(action="DELETE", model=model_name, object_id=object_id, user=user, object_data=object_data)

    @classmethod
    def log_action(cls, model_name, object_id, user=None, object_data=None):
        return cls.objects.create(action="ACTION", model=model_name, object_id=object_id, user=user, object_data=object_data)

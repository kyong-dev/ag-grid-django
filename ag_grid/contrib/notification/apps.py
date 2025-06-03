from django.apps import AppConfig


class NotificationConfig(AppConfig):
    name = "ag_grid.contrib.notification"
    label = "ag_grid_notification"
    verbose_name = "AG Grid Notifications"

    def ready(self):
        # Import signal handlers when Django starts
        import ag_grid.contrib.notification.signals

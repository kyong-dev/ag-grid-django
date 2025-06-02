from django.apps import apps

# Global registry that stores AG Grid configurations for models
AGGRID_REGISTRY = {}


def register(model):
    """
    Decorator for registering AG Grid configurations for models

    Usage:
        @register(YourModel)
        class YourModelGrid:
            # Configuration here

    Args:
        model: The Django model class to register the configuration for

    Returns:
        Decorator function that registers the AG Grid class
    """

    def decorator(aggrid_cls):
        AGGRID_REGISTRY[model] = aggrid_cls()
        return aggrid_cls

    return decorator


def get_config(model):
    """
    Get the AG Grid configuration for a specific model

    Args:
        model: The Django model class

    Returns:
        The registered AG Grid configuration instance or None if not found
    """
    return AGGRID_REGISTRY.get(model)


class ResourceRegistry:
    """
    Registry for Excel export resources

    This class manages the registration and retrieval of export resources
    that define how models should be exported to Excel.
    """

    def __init__(self):
        """Initialize an empty registry dictionary"""
        self._registry = {}

    def register(self, model_or_path, resource_class, **kwargs):
        """
        Register a resource class for a model

        Args:
            model_or_path: Either a model class or a string in format 'app_label.model_name'
            resource_class: The ModelResource class to use for Excel exports
            **kwargs: Additional options to pass to the resource class constructor

        Raises:
            ValueError: If the model path is invalid
        """
        if isinstance(model_or_path, str):
            try:
                app_label, model_name = model_or_path.split(".")
                model = apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                raise ValueError(f"Invalid model path: {model_or_path}")
        else:
            model = model_or_path

        # Warning if model is already registered
        if model in self._registry:
            import warnings

            warnings.warn(f"Resource for model {model._meta.label} is already registered. Overwriting.")

        # Create and register resource instance
        resource_instance = resource_class(**kwargs)
        self._registry[model] = resource_instance

    def unregister(self, model):
        """
        Remove a registered model resource

        Args:
            model: The model class to unregister
        """
        if model in self._registry:
            del self._registry[model]

    def get_resource(self, model_or_path):
        """
        Get the resource for a specific model

        Args:
            model_or_path: Either a model class or a string in format 'app_label.model_name'

        Returns:
            The registered resource instance or None if not found
        """
        if isinstance(model_or_path, str):
            try:
                app_label, model_name = model_or_path.split(".")
                model = apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                return None
        else:
            model = model_or_path

        return self._registry.get(model)

    def get_resources(self):
        """
        Get all registered resources

        Returns:
            Dictionary mapping model classes to their resource instances
        """
        return self._registry

    def is_registered(self, model):
        """
        Check if a model has a registered resource

        Args:
            model: The model class to check

        Returns:
            Boolean indicating if the model is registered
        """
        return model in self._registry


# Create global resource registry instance
resource_registry = ResourceRegistry()

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model


class ModelField:
    """
    Class representing a model field for Excel export
    """

    def __init__(self, attribute=None, column_name=None, display_method=None, default=None, export_only=False, width=None, format=None):
        """
        Initialize field settings

        Args:
            attribute (str): Model attribute name (dot notation for related fields: 'user.email')
            column_name (str): Column name to display in Excel
            display_method (callable): Function to display value (lambda obj: f"{obj.first_name} {obj.last_name}")
            default: Default value (when None)
            export_only (bool): Whether this field is only for export and not for import
            width (int): Column width in Excel
            format (str): Cell format (e.g., date format 'yyyy-mm-dd')
        """
        self.attribute = attribute
        self.column_name = column_name
        self.display_method = display_method
        self.default = default
        self.export_only = export_only
        self.width = width
        self.format = format

    def get_value(self, obj):
        """
        Extract field value from the given object
        """
        if self.display_method:
            return self.display_method(obj)

        if not self.attribute:
            return self.default

        # Process dot notation attributes (user.profile.name)
        attrs = self.attribute.split(".")
        value = obj

        for attr in attrs:
            try:
                value = getattr(value, attr)
                # Call if it's a callable but not a class
                if callable(value) and not isinstance(value, type):
                    value = value()
            except (AttributeError, KeyError):
                return self.default

        return value if value is not None else self.default


class ModelResource:
    """
    Base model resource class for Excel export
    """

    # Resource configuration
    model = None
    fields = []
    exclude = []
    export_order = None

    # Output settings
    title = None

    def __init__(self):
        if not self.model:
            raise ImproperlyConfigured("The model class attribute must be specified when implementing ModelResource.")

        self._meta = self.get_meta()
        self.fields_dict = self._get_fields_dict()

    def get_meta(self):
        """Get metadata information"""
        return {
            "model": self.model,
            "fields": self.fields,
            "exclude": self.exclude,
            "export_order": self.export_order or list(self._get_fields_dict().keys()),
            "title": self.title or self.model._meta.verbose_name_plural.title(),
        }

    def get_export_headers(self):
        """Return list of headers to be used in Excel export"""
        headers = []
        for field_name in self._meta["export_order"]:
            field = self.fields_dict.get(field_name)
            if field:
                header = field.column_name or field_name.replace("_", " ").title()
                headers.append(header)
        return headers

    def _get_fields_dict(self):
        """Create field name -> ModelField object mapping dictionary"""
        fields_dict = {}

        # Process directly specified fields
        for item in self.fields:
            if isinstance(item, tuple) and len(item) == 2:
                field_name, field_obj = item
                if isinstance(field_obj, ModelField):
                    fields_dict[field_name] = field_obj
                else:
                    # Convert tuple format (field_name, display_name) to ModelField object
                    fields_dict[field_name] = ModelField(attribute=field_name, column_name=field_obj)
            elif isinstance(item, str):
                # If only string is specified, create ModelField with the same attribute name
                fields_dict[item] = ModelField(attribute=item)

        # If no fields specified, use all model fields
        if not fields_dict:
            for field in self.model._meta.fields:
                if field.name not in self.exclude and not field.name.endswith("_ptr"):
                    fields_dict[field.name] = ModelField(attribute=field.name, column_name=field.verbose_name.title() if hasattr(field, "verbose_name") else field.name.replace("_", " ").title())

        return fields_dict

    def get_queryset(self):
        """Return base queryset for the export data"""
        return self.model.objects.all()

    def get_export_data(self, queryset=None):
        """Generate export data"""
        queryset = queryset or self.get_queryset()
        data = []

        for obj in queryset:
            row = {}
            for field_name in self._meta["export_order"]:
                field = self.fields_dict.get(field_name)
                if field:
                    row[field_name] = field.get_value(obj)
            data.append(row)

        return data

    def get_field_formats(self):
        """Return format information for each field"""
        formats = {}
        for field_name, field in self.fields_dict.items():
            if field.format:
                formats[field_name] = field.format
            if field.width:
                if field_name not in formats:
                    formats[field_name] = {}
                formats[field_name]["width"] = field.width
        return formats

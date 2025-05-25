# AG Grid Django Integration Guide

This README provides a comprehensive guide on integrating AG Grid with your Django project for creating dynamic, interactive data tables with CRUD capabilities.

## Table of Contents

- Installation
- Basic Configuration
- Model Registration
- URL Configuration
- Permissions Setup
- Frontend Integration
- Advanced Configuration

## Installation

### 1. Install the package

```bash
pip install ag-grid-django  
```

### 2. Add the app to your INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'ag_grid',
    # ...
]
```

### 3. Install required dependencies

```bash
pip install djangorestframework
pip install drf-yasg  # For Swagger documentation
```

## Basic Configuration

### Create a configuration file

Create a file named `aggrid_admin.py` in each app where you want to use AG Grid:

```python
# yourapp/aggrid_admin.py
from ag_grid.grid import AgGrid
from ag_grid.registry import register
from yourapp.models import YourModel

@register(YourModel)
class YourModelAG(AgGrid):
    list_display = ('id', 'field1', 'field2', 'related_model__field')
    editable = ('field1', 'field2')
    sortable = ('field1', 'field2')
    
    # Optional: Configure form fields for adding/editing
    form_fields = {
        "field1": {
            "type": "text",
            "label": "Field One",
            "required": True,
            "placeholder": "Enter field one",
            "validation": {"required": "This field is required"}
        },
        "field2": {
            "type": "number",
            "label": "Field Two",
            "required": True,
            "validation": {"min": {"value": 0, "message": "Must be positive"}}
        },
        # Add more fields as needed
    }
    
    # Optional: Optimize queries
    @classmethod
    def get_queryset(cls, model):
        return model.objects.select_related('related_model')
```

### Ensure app configuration loads your AG Grid settings

```python
# yourapp/apps.py
from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'yourapp'
    
    def ready(self):
        # Import aggrid_admin to register models
        import yourapp.aggrid_admin
```

Make sure your `__init__.py` uses this config:

```python
# yourapp/__init__.py
default_app_config = 'yourapp.apps.YourAppConfig'
```

## Model Registration

For each model you want to manage with AG Grid:

1. Import your model and the AG Grid components
2. Decorate a class with `@register(YourModel)`
3. Define display configuration:
   - `list_display`: Fields to show in the grid
   - `editable`: Fields that can be edited inline
   - `sortable`: Fields that can be sorted
   - `form_fields`: Configuration for form fields in add/edit forms


Example:

```python
@register(Product)
class ProductAG(AgGrid):
    list_display = ("id", "name", "category__name", "price", "quantity")
    editable = ("price", "quantity")
    sortable = ("name", "price", "quantity")
    
    form_fields = {
        "name": {
            "type": "text",
            "label": "Product Name",
            "required": True,
            "placeholder": "Enter product name",
            "validation": {"required": "Product name is required"}
        },
        # More fields...
    }
```

## URL Configuration

### 1. Include AG Grid URLs in your project's main URLs

```python
# yourproject/urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path("api/ag-grid/", include("ag_grid.urls", namespace="ag_grid")),
    # ...
]
```

## Permissions Setup

### 1. Ensure proper model permissions exist

Make sure your models have the standard Django permissions (view, add, change, delete).

### 2. Configure your authentication system

The AG Grid views use Django REST Framework's permission system. Configure your authentication in settings.py:
Make sure you are using simplejwt to use AgGrid Package Permission

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}
```

### 3. Assign permissions to users

In Django Admin, assign the appropriate permissions to your users:
- `yourapp.view_yourmodel`
- `yourapp.add_yourmodel`
- `yourapp.change_yourmodel`
- `yourapp.delete_yourmodel`

## Frontend Integration

### API Endpoints

The following endpoints are available for each registered model:

1. `GET /api/aggrid/{app_label}/{model_name}/headers/` - Get grid headers
2. `GET /api/aggrid/{app_label}/{model_name}/form-fields/` - Get form field configuration
3. `PATCH /api/aggrid/{app_label}/{model_name}/{id}/update/` - Update a field
4. `POST /api/aggrid/{app_label}/{model_name}/create/` - Create a new instance
5. `DELETE /api/aggrid/{app_label}/{model_name}/{id}/delete/` - Delete an instance


## Advanced Configuration

### Custom Field Types

The system maps Django field types to AG Grid types using these mappings:

```python
FIELD_TYPE_MAP = {
    "AutoField": "number",
    "BigIntegerField": "number",
    "IntegerField": "number",
    "FloatField": "number",
    "DecimalField": "number",
    "CharField": "text",
    "TextField": "text",
    "EmailField": "text",
    "SlugField": "text",
    "BooleanField": "boolean",
    "DateField": "date",
    "DateTimeField": "datetime",
    "ForeignKey": "fk",
    "OneToOneField": "fk",
    "ManyToManyField": "m2m",
}

FILTER_TYPE_MAP = {
    "AutoField": "agNumberColumnFilter",
    "BigIntegerField": "agNumberColumnFilter",
    "IntegerField": "agNumberColumnFilter",
    "FloatField": "agNumberColumnFilter",
    "DecimalField": "agNumberColumnFilter",
    "DateField": "agDateColumnFilter",
    "DateTimeField": "agDateColumnFilter",
}
```

### Change Logging

The system automatically logs all changes to a `GridEditLog` model:

- Creation of records
- Updates to field values
- Deletion of records

This provides an audit trail of all changes made through the AG Grid interface.

## Troubleshooting

### Common Issues

1. **Grid config not found error**
   - Ensure your `aggrid_admin.py` file is being loaded
   - Check that you've properly registered your model

2. **Permission errors**
   - Verify the user has the appropriate permissions
   - Check authentication setup

3. **Field not editable**
   - Make sure the field is included in the `editable` tuple

For more help, check the documentation or open an issue in the project repository.

Similar code found with 1 license type
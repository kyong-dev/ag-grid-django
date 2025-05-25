from django.apps import apps
from django.utils.translation import gettext_lazy as _

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView as BaseAPIView

from .log import GridEditLog
from .permissions import AgGridModelPermission
from .registry import get_config

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


class APIView(BaseAPIView):

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to ensure permissions are checked"""
        # Store kwargs for permission class to access
        self.kwargs = kwargs

        # Explicitly check permissions before proceeding
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                return self.permission_denied(request, message=getattr(permission, "message", lambda r, v: None)(request, self))

        return super().dispatch(request, *args, **kwargs)

    def permission_denied(self, request, message=None, code=None):
        """
        Override permission_denied to provide clearer error messages
        """
        if message is None and hasattr(self.permission_classes[0], "message"):
            message = self.permission_classes[0]().message(request, self)

        response = {
            "error": "Permission denied",
            "detail": message or "You do not have permission to perform this action",
            "required_permissions": [f"{self.kwargs.get('app_label')}.{op}_{self.kwargs.get('model_name').lower()}" for op in ["view", "add", "change", "delete"]],
        }

        # Create a Response with a renderer explicitly set
        response_obj = Response(response, status=status.HTTP_403_FORBIDDEN)
        response_obj.accepted_renderer = JSONRenderer()
        response_obj.accepted_media_type = "application/json"
        response_obj.renderer_context = {
            "request": request,
            "view": self,
        }

        return response_obj


class AgGridHeaderAPIView(APIView):
    permission_classes = [AgGridModelPermission]

    @swagger_auto_schema(
        operation_description=_("Get headers for AgGrid based on model configuration"),
        operation_summary=_("Get AgGrid Headers"),
        responses={
            200: openapi.Response(
                description="List of headers for the grid",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "field": openapi.Schema(type=openapi.TYPE_STRING, description="Field name"),
                            "headerName": openapi.Schema(type=openapi.TYPE_STRING, description="Header name"),
                            "editable": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Is field editable"),
                            "sortable": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Is field sortable"),
                            "type": openapi.Schema(type=openapi.TYPE_STRING, description="Field type"),
                            "filter": openapi.Schema(type=openapi.TYPE_STRING, description="Filter type"),
                        },
                    ),
                ),
            ),
            404: openapi.Response(description="Model or configuration not found", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        },
        tags=["AgGrid"],
    )
    def get(self, request, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return Response({"error": "Model not found"}, status=status.HTTP_404_NOT_FOUND)

        config = get_config(model)
        if not config:
            return Response({"error": "Grid config not found"}, status=status.HTTP_404_NOT_FOUND)

        field_list = config.get_list_display()

        if field_list and isinstance(field_list[0], dict):
            return Response(field_list)

        if isinstance(field_list, (list, tuple)):
            field_list = list(field_list)
        else:
            field_list = [f.name for f in model._meta.fields]

        headers = []
        for field in model._meta.get_fields():
            if not hasattr(field, "name"):
                continue
            if field.name not in field_list:
                continue

            internal_type = field.get_internal_type()
            field_type = FIELD_TYPE_MAP.get(internal_type, "text")

            filter_type = FILTER_TYPE_MAP.get(internal_type, "agTextColumnFilter")

            headers.append(
                {
                    "field": field.name,
                    "headerName": field.verbose_name.title() or field.name,
                    "editable": field.name in config.get_editable_fields(),
                    "sortable": field.name in config.get_sortable_fields(),
                    "type": field_type,
                    "filter": filter_type,
                }
            )
        return Response(headers)


class AgGridUpdateAPIView(APIView):
    permission_classes = [AgGridModelPermission]

    @swagger_auto_schema(
        operation_description=_("Update a specific field of a model instance"),
        operation_summary=_("Update Model Field"),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["field", "value"],
            properties={
                "field": openapi.Schema(type=openapi.TYPE_STRING, description="Field name to update"),
                "value": openapi.Schema(type=openapi.TYPE_STRING, description="New value for the field"),
            },
        ),
        responses={
            200: openapi.Response(description="Update successful", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True)})),
            400: openapi.Response(description="Invalid data provided", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
            404: openapi.Response(
                description="Object not found", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING, default="Object not found")})
            ),
            403: openapi.Response(description="Authentication required", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)})),
        },
        tags=["AgGrid"],
    )
    def patch(self, request, app_label, model_name, pk):
        try:
            model = apps.get_model(app_label, model_name)
            config = get_config(model)
            instance = model.objects.get(pk=pk)
        except Exception:
            return Response({"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND)

        # Handle the new format with "field" and "value" keys
        field = request.data.get("field")
        value = request.data.get("value")

        if not field:
            return Response({"error": "Missing 'field' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        editable_fields = config.get_editable_fields()
        if field in editable_fields:
            old_value = getattr(instance, field)
            setattr(instance, field, value)
            if str(old_value) != str(value):
                # 로그 저장
                GridEditLog.log_update(
                    model_name=f"{app_label}.{model_name}", object_id=str(pk), field=field, old_value=str(old_value), new_value=str(value), user=request.user if request.user.is_authenticated else None
                )
            instance.save()
            return Response({"success": True, "field": field, "old_value": str(old_value), "new_value": str(value)})
        else:
            return Response({"error": f"Field '{field}' is not editable"}, status=status.HTTP_400_BAD_REQUEST)


def _get_form_field_type(field):
    """Map Django field types to form field types."""
    internal_type = field.get_internal_type()
    if internal_type in ["CharField", "TextField", "SlugField", "EmailField", "URLField"]:
        return "textarea" if internal_type == "TextField" else "text"
    elif internal_type in ["IntegerField", "PositiveIntegerField", "PositiveSmallIntegerField", "SmallIntegerField", "BigIntegerField"]:
        return "number"
    elif internal_type in ["DecimalField", "FloatField"]:
        return "number"
    elif internal_type in ["BooleanField", "NullBooleanField"]:
        return "checkbox"
    elif internal_type in ["DateField"]:
        return "date"
    elif internal_type in ["DateTimeField"]:
        return "datetime-local"
    elif internal_type in ["TimeField"]:
        return "time"
    elif internal_type in ["ForeignKey", "OneToOneField"]:
        return "select"
    elif internal_type in ["ManyToManyField"]:
        return "multiselect"
    else:
        return "text"


class AgGridCreateAPIView(APIView):
    """API view for creating a new model instance."""

    permission_classes = [AgGridModelPermission]

    @swagger_auto_schema(
        operation_description=_("Create a new model instance"),
        operation_summary=_("Create Model Instance"),
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, description="Form data for creating a new instance", additional_properties=openapi.Schema(type=openapi.TYPE_STRING)),
        responses={
            201: openapi.Response(
                description="Object created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the created object"),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid data provided",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                        "field_errors": openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))),
                    },
                ),
            ),
            404: openapi.Response(description="Model not found", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        },
        tags=["AgGrid"],
    )
    def post(self, request, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
            config = get_config(model)
        except LookupError:
            return Response({"error": "Model not found"}, status=status.HTTP_404_NOT_FOUND)

        if not config:
            return Response({"error": "Grid config not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create a new instance with the provided data
        try:
            # Start with an empty instance
            instance = model()

            # Set fields from the request data
            for field_name, field_value in request.data.items():
                if hasattr(instance, field_name) and field_name != "id":
                    setattr(instance, field_name, field_value)

            # Save the instance
            instance.save()

            # Log the creation
            object_data = {field: str(getattr(instance, field)) for field in request.data.keys() if hasattr(instance, field)}
            GridEditLog.log_create(model_name=f"{app_label}.{model_name}", object_id=str(instance.pk), user=request.user if request.user.is_authenticated else None, object_data=object_data)

            return Response({"success": True, "id": instance.pk, "message": f"{model_name} created successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Failed to create {model_name}", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AgGridDeleteAPIView(APIView):
    """API view for deleting a model instance."""

    permission_classes = [AgGridModelPermission]

    @swagger_auto_schema(
        operation_description=_("Delete a specific model instance"),
        operation_summary=_("Delete Model Instance"),
        responses={
            200: openapi.Response(
                description="Object deleted successfully",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True), "message": openapi.Schema(type=openapi.TYPE_STRING)}),
            ),
            404: openapi.Response(description="Object not found", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
            403: openapi.Response(description="Permission denied", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        },
        tags=["AgGrid"],
    )
    def delete(self, request, app_label, model_name, pk):
        try:
            model = apps.get_model(app_label, model_name)
            instance = model.objects.get(pk=pk)
        except LookupError:
            return Response({"error": "Model not found"}, status=status.HTTP_404_NOT_FOUND)
        except model.DoesNotExist:
            return Response({"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND)

        # Save object data before deletion for logging
        try:
            # Get serializable data from the instance
            object_data = {}
            for field in model._meta.fields:
                field_name = field.name
                value = getattr(instance, field_name)
                object_data[field_name] = str(value)

            # Delete the instance
            instance.delete()

            # Log the deletion
            GridEditLog.log_delete(model_name=f"{app_label}.{model_name}", object_id=str(pk), user=request.user if request.user.is_authenticated else None, object_data=object_data)

            return Response({"success": True, "message": f"{model_name} deleted successfully"})

        except Exception as e:
            return Response({"error": f"Failed to delete {model_name}", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AgGridFormFieldsAPIView(APIView):
    """API view for getting form field information for a model."""

    permission_classes = [AgGridModelPermission]

    @swagger_auto_schema(
        operation_description=_("Get form field requirements for a model"),
        operation_summary=_("Get Form Field Requirements"),
        responses={
            200: openapi.Response(
                description="Form field requirements",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "fields": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "name": openapi.Schema(type=openapi.TYPE_STRING),
                                    "type": openapi.Schema(type=openapi.TYPE_STRING),
                                    "label": openapi.Schema(type=openapi.TYPE_STRING),
                                    "required": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    "placeholder": openapi.Schema(type=openapi.TYPE_STRING),
                                    "validation": openapi.Schema(type=openapi.TYPE_OBJECT),
                                    "options": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                                    "options_endpoint": openapi.Schema(type=openapi.TYPE_STRING),
                                },
                            ),
                        ),
                        "model_info": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "app_label": openapi.Schema(type=openapi.TYPE_STRING),
                                "model_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "verbose_name": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            404: openapi.Response(description="Model or configuration not found", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        },
        tags=["AgGrid"],
    )
    def get(self, request, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return Response({"error": "Model not found"}, status=status.HTTP_404_NOT_FOUND)

        config = get_config(model)
        if not config:
            return Response({"error": "Grid config not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get form fields from config or generate from model
        form_fields = {}
        if hasattr(config, "form_fields"):
            form_fields = config.form_fields
        else:
            # Generate basic form fields from model if not defined
            for field in model._meta.fields:
                if field.name == "id" or field.name.endswith("_ptr"):
                    continue

                field_config = {
                    "type": _get_form_field_type(field),
                    "label": field.verbose_name.title() if hasattr(field, "verbose_name") else field.name.replace("_", " ").title(),
                    "required": not field.blank,
                    "placeholder": f'Enter {field.verbose_name if hasattr(field, "verbose_name") else field.name}',
                }

                form_fields[field.name] = field_config

        # Convert to a list format with field names included
        fields_list = []
        for field_name, field_config in form_fields.items():
            field_data = field_config.copy()
            field_data["name"] = field_name
            fields_list.append(field_data)

        # Add model information
        model_info = {
            "app_label": app_label,
            "model_name": model_name,
            "verbose_name": model._meta.verbose_name.title(),
            "verbose_name_plural": model._meta.verbose_name_plural.title(),
            "create_url": f"/api/aggrid/{app_label}/{model_name}/create/",
            "update_url_template": f"/api/aggrid/{app_label}/{model_name}/{{id}}/update/",
            "delete_url_template": f"/api/aggrid/{app_label}/{model_name}/{{id}}/delete/",
        }

        return Response({"fields": fields_list, "model_info": model_info})

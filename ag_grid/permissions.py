import logging

from django.apps import apps

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class AgGridModelPermission(BasePermission):
    """
    Custom permission class for AG Grid API operations.
    Uses token authentication and checks model-specific permissions.
    """

    def authenticate_token(self, request):
        """Extract and validate the token from request headers"""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer ") and not auth_header.startswith("Bearer "):
            logger.warning("No valid authorization header found")
            return None

        try:
            # Use DRF's TokenAuthentication to validate the token
            token_auth = TokenAuthentication()
            user_auth_tuple = token_auth.authenticate(request)
            if user_auth_tuple is not None:
                user, token = user_auth_tuple
                return user
        except AuthenticationFailed as e:
            logger.warning(f"Token authentication failed: {str(e)}")
            return None

        return None

    def has_permission(self, request, view):
        # First try to get user from token
        user = self.authenticate_token(request)

        # If token auth failed, fall back to request.user (for session auth)
        if user is None:
            user = request.user

        # Log the permission check
        logger.info(f"Checking permissions for user: {user}, authenticated: {user.is_authenticated}")

        if not user.is_authenticated:
            logger.warning("Permission denied: User not authenticated")
            return False

        if not user.is_staff:
            logger.warning(f"Permission denied: User {user.username} is not staff")
            return False

        app_label = view.kwargs.get("app_label")
        model_name = view.kwargs.get("model_name")

        if not (app_label and model_name):
            logger.warning("Permission denied: Missing app_label or model_name")
            return False

        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            logger.warning(f"Permission denied: Model {app_label}.{model_name} not found")
            return False

        # Check model-specific permissions based on HTTP method
        permission_codename = None
        if request.method == "GET":
            permission_codename = f"{app_label}.view_{model_name.lower()}"
        elif request.method == "POST":
            permission_codename = f"{app_label}.add_{model_name.lower()}"
        elif request.method in ["PUT", "PATCH"]:
            permission_codename = f"{app_label}.change_{model_name.lower()}"
        elif request.method == "DELETE":
            permission_codename = f"{app_label}.delete_{model_name.lower()}"

        has_perm = user.has_perm(permission_codename)

        # Make sure we're actually returning False when permission is denied
        if not has_perm:
            logger.warning(f"PERMISSION DENIED: {user} does not have {permission_codename}")
            return False

        return has_perm

    def has_object_permission(self, request, view, obj):
        # First try to get user from token
        user = self.authenticate_token(request)

        # If token auth failed, fall back to request.user (for session auth)
        if user is None:
            user = request.user

        app_label = view.kwargs.get("app_label")
        model_name = view.kwargs.get("model_name")

        permission_codename = None
        if request.method == "GET":
            permission_codename = f"{app_label}.view_{model_name.lower()}"
        elif request.method in ["PUT", "PATCH"]:
            permission_codename = f"{app_label}.change_{model_name.lower()}"
        elif request.method == "DELETE":
            permission_codename = f"{app_label}.delete_{model_name.lower()}"

        return user.has_perm(permission_codename)

    def message(self, request, view):
        """
        Return a descriptive message about why permission was denied.
        """
        # First try to get user from token
        user = self.authenticate_token(request)

        # If token auth failed, fall back to request.user
        if user is None:
            user = request.user

        app_label = view.kwargs.get("app_label")
        model_name = view.kwargs.get("model_name")

        if not user.is_authenticated:
            return "Authentication required. Please provide a valid token."

        if not user.is_staff:
            return "Staff status required for API access."

        operation = {"GET": "view", "POST": "add", "PUT": "change", "PATCH": "change", "DELETE": "delete"}.get(request.method, "unknown")

        perm = f"{app_label}.{operation}_{model_name.lower()}"
        return f"Missing permission: {perm}"

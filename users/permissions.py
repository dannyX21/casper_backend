from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import MethodNotAllowed
from users.models import User

class UserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_admin:
            return True

        if request.user.is_authenticated:
            if request.method in SAFE_METHODS or request.method in ('PATCH', 'PUT'):
                return True

            else:
                raise MethodNotAllowed(request.method)

        if request.method in ('POST',):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_admin:
            return True

        if obj == request.user:
            return True

        return False

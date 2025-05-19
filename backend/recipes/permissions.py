from rest_framework.permissions import BasePermission
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import GenericViewSet
from rest_framework.request import Request


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.author == request.user


class ReadOnly(BasePermission):
    """Проверка на разрешение только редактирования."""

    def has_permission(self, request: Request, view: GenericViewSet) -> bool:
        return request.method in SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user
            and request.user.is_staff
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

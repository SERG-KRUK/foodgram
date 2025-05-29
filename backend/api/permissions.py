"""Кастомные permissions для REST API."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает изменение рецепта только его автору."""

    def has_object_permission(self, request, view, obj):
        """Разрешение для автора или только чтение."""
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )

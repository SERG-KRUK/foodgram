"""Кастомные permissions для REST API."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает изменение рецепта только его автору."""

    def has_object_permission(self, request, view, obj):
        """Проверяет, является ли пользователь автором рецепта."""
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user

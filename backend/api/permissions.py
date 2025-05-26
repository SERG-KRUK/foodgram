"""Кастомные permissions для REST API."""

from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает изменение рецепта только его автору."""

    def has_object_permission(self, request, view, obj):
        """Проверяет, является ли пользователь автором рецепта."""
        return obj.author == request.user

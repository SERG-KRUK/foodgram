"""Модуль с кастомными permissions для REST API."""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает доступ на чтение всем, а изменение только автору объекта."""

    def has_object_permission(
            self, request: Request, view: GenericViewSet, obj) -> bool:
        """
        Проверяет права доступа к объекту.

        Args:
            request: Запрос от клиента
            view: ViewSet, обрабатывающий запрос
            obj: Объект, к которому проверяются права

        Returns:
            bool: True если доступ разрешен, False если запрещен
        """
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class ReadOnly(BasePermission):
    """Разрешает только безопасные методы (GET, HEAD, OPTIONS)."""

    def has_permission(self, request: Request, view: GenericViewSet) -> bool:
        """
        Проверяет, является ли метод запроса безопасным.

        Args:
            request: Запрос от клиента
            view: ViewSet, обрабатывающий запрос

        Returns:
            bool: True если метод безопасный, False если нет
        """
        return request.method in SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Разрешает доступ на чтение всем, а изменение только администраторам."""

    def has_permission(self, request: Request, view: GenericViewSet) -> bool:
        """
        Проверяет права доступа к view.

        Args:
            request: Запрос от клиента
            view: ViewSet, обрабатывающий запрос

        Returns:
            bool: True если доступ разрешен, False если запрещен
        """
        return (request.method in SAFE_METHODS
                or request.user
                and request.user.is_staff)


class IsAdmin(BasePermission):
    """Разрешает доступ только администраторам."""

    def has_permission(self, request: Request, view: GenericViewSet) -> bool:
        """
        Проверяет, является ли пользователь администратором.

        Args:
            request: Запрос от клиента
            view: ViewSet, обрабатывающий запрос

        Returns:
            bool: True если пользователь администратор, False если нет
        """
        return request.user and request.user.is_staff

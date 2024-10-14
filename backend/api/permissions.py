"""Кастомные права для пользователей."""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Кастомное разрешение.

    - Безопасные методы (GET, HEAD, OPTIONS) доступны всем.
    - Остальные методы (POST, PUT, PATCH, DELETE) доступны только автору.
    """

    def has_permission(self, request, view):
        """функция для работы с общим доступом."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """функция для работы с доступомк конкретному объекту."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

"""Кастомные права для пользователей."""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Кастомное разрешение.

    - Безопасные методы (GET, HEAD, OPTIONS) доступны всем.
    - Остальные методы (POST, PUT, PATCH, DELETE) доступны только автору.
    """

    def has_object_permission(self, request, view, obj):
        """Проверка доступа к конкретному объекту."""
        return (
            request.method in
            permissions.SAFE_METHODS or obj.author == request.user
        )

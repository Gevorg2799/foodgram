"""Кастомные валидаторы."""

import re

from django.core.exceptions import ValidationError


def validate_username(value):
    """Валидатор ддля username пользователя."""
    if not re.match(r'^[\w.-]+$', value):
        raise ValidationError(
            'Имя пользователя может содержать только латинские буквы, цифры')
    return value

"""Apps для бэкенда."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Класс для конфигурации."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи и подписки'

"""Apps для бэкенда."""

from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Класс для конфигурации."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = 'Рецепты, ингредиенты и теги'

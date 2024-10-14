"""Кстомная пагинация."""

from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Кастомный пагинатор для поддержки параметров page и limit."""

    page_size = 5  # По умолчанию 10 объектов на страницу
    page_size_query_param = 'limit'
    max_page_size = 50  # Максимальное количество объектов на странице

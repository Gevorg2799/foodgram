"""Кстомная пагинация."""

from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGINATION_LIMIT


class ProjectPagination(PageNumberPagination):
    """Кастомный пагинатор для поддержки параметров page и limit."""

    page_size = PAGINATION_LIMIT  # По умолчанию 10 объектов на страницу
    page_size_query_param = 'limit'

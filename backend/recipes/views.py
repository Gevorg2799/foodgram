"""Views-классы."""

from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import urlsafe_base64_decode
from .models import Recipe


class ShortLinkRedirectView(View):
    """Для редиректа короткой ссылки."""

    def get(self, request, short_code, *args, **kwargs):
        """Получение URL и редирект."""
        recipe_id = urlsafe_base64_decode(short_code).decode('utf-8')
        recipe = get_object_or_404(Recipe, id=int(recipe_id))
        recipe_url = request.build_absolute_uri(f"/recipes/{recipe.id}/")
        return redirect(recipe_url)

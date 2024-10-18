"""Работа с фильтрами проекта."""

from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтры для рецептов."""

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(), field_name='tags__slug',
        to_field_name='slug')

    class Meta:
        """Свойства."""

        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует по тому, находится ли рецепт в избранном."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favoriterecipe__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует по тому, находится ли рецепт в корзине покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shoppingcart__user=user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Поиск по названию без учета регистра."""

    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        """Свойства."""

        model = Ingredient
        fields = ['name']

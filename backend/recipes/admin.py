"""Работа с моделями в админке."""

from django.contrib import admin

from .models import Ingredient, IngredientRecipe, MyFavoriteRecipe, Recipe, Tag


class IngredientRecipeinAdmin(admin.StackedInline):
    """Количество ингредиентов в рецепте."""

    model = IngredientRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Отображение рецепта."""

    inlines = (IngredientRecipeinAdmin,)
    list_display = (
        'name',
        'text',
        'cooking_time',
        'author',
        'ingredient_in_list',
        'tags_in_list',
        'image'
    )
    filter_horizontal = ('tags',)
    list_filter = ('tags',)
    search_fields = ('author__first_name', 'author__last_name', 'name')

    @admin.display(description='Теги')
    def tags_in_list(self, obj):
        """Теги в рецепте."""
        a = ', '.join([tag.name for tag in obj.tags.all()])
        if len(a) < 1:
            a = 'Нет тегов'
        return a

    @admin.display(description='Ингредиенты')
    def ingredient_in_list(self, obj):
        """Ингредиенты в рецепте."""
        return (
            [f' {ingred.ingredient.name}'
             f'({ingred.amount}{ingred.ingredient.measurement_unit}.)'
             for ingred in obj.ingredients_amout.all()]
        )


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    """Отображенеи отдельно количества ингредиентов в рецепте."""

    list_display = ('id', 'recipe', 'ingredient', 'amount',)


@admin.register(MyFavoriteRecipe)
class MyFavoriteRecipeAdmin(admin.ModelAdmin):
    """Отображение избранных рецептов."""

    list_display = ('id', 'recipe', 'author')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Отображение тегов."""

    list_display = ('id', 'name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Отображение ингредиентов."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)

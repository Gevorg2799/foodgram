from django.contrib import admin

from .models import (Tag, Ingredient, Recipe,
                     IngredientRecipe, MyFavoriteRecipe, ShoppingCart)


class IngredientRecipeinAdmin(admin.StackedInline):
    model = IngredientRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
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
        a = ', '.join([tag.name for tag in obj.tags.all()])
        if len(a) < 1:
            a = 'Нет тегов'
        return a

    @admin.display(description='Ингредиенты')
    def ingredient_in_list(self, obj):
        return (
            [f' {ingred.ingredient.name}'
             f'({ingred.amount}{ingred.ingredient.measurement_unit}.)'
             for ingred in obj.ingredients_amout.all()]
        )


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',)


@admin.register(MyFavoriteRecipe)
class MyFavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'author')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')


@admin.register(ShoppingCart)
class MyFavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user')


# admin.site.register(Tag, TagAdmin)
# admin.site.register(Ingredient, IngredientAdmin)
# admin.site.register(Recipe, RecipeAdmin)
# admin.site.register(IngredientRecipe, IngredientRecipeAdmin)

# list_display = (
#     'id',
#     'username',
#     'email',
#     'first_name',
#     'last_name',
#     'is_staff',
#     'is_superuser',
#     'date_joined',
# )
# list_filter = ('is_staff', 'is_superuser',)
# search_fields = ('username', 'email', 'first_name', 'last_name',)
# list_display_links = ('username',)
# list_editable = (
#     'is_staff',
#     'is_superuser',
# )
# date_hierarchy = 'date_joined'
# exclude = ('password', 'date_joined',)

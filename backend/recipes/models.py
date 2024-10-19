"""Модели приложение рецепты."""

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram.constants import (LENGTH_INGREDIENT_MEAS_UNIT,
                                LENGTH_INGREDIENT_NAME, LENGTH_RECIPE_NAME,
                                LENGTH_TAGS_NAME, LENGTH_TAGS_SLUG)

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField('Название', max_length=LENGTH_INGREDIENT_NAME)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=LENGTH_INGREDIENT_MEAS_UNIT)

    class Meta:
        """Свойства."""

        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                name='Unique_ingredient',
                fields=('name', 'measurement_unit')),
        ]

    def __str__(self):
        """Отображение модели."""
        return f'{self.name}({self.measurement_unit})'


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        'Название тега',
        unique=True,
        max_length=LENGTH_TAGS_NAME
    )
    slug = models.SlugField(
        'Слаг тега',
        max_length=LENGTH_TAGS_SLUG,
        unique=True
    )

    class Meta:
        """Свойства."""

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                name='Unique_tags',
                fields=('name', 'slug')),
        ]

    def __str__(self):
        """Отображение модели."""
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    name = models.CharField(
        'Название',
        max_length=LENGTH_RECIPE_NAME
    )
    text = models.TextField(
        'Описание',
        help_text='Опишите рецепт приготовления блюда',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Укажите время не меньше 1 минуты'
            ),
            MaxValueValidator(
                limit_value=32767,
                message='Время приготовления не может быть больше 32767 минут'
            )
        ],
        help_text='Время приготовления укажите в минутах'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'

    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        help_text='Выберите один или несколько тегов'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
        help_text='Выберите нужные игредиенты и укажите количество в рецепте'
    )
    image = models.ImageField(
        'Картинка блюда',
        upload_to='recipes/images/',
        help_text='загрузите изображение вашего блюда'
    )

    class Meta:
        """Свойства."""

        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('name', 'cooking_time')

    def __str__(self):
        """Отображение модели."""
        return self.name


class IngredientRecipe(models.Model):
    """Моедль для связи ингредиента и рецепта."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_amout',
        verbose_name='Ингредиент'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_amout',
        verbose_name='Рецепт'
    )

    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Укажите количество не меньше 1'
            )],
        help_text='Введите килество ингредиента'
    )

    class Meta:
        """Свойства."""

        verbose_name = 'Количетсво ингередиента в рецепте'
        verbose_name_plural = 'Количество ингередиентов в рецепте'
        constraints = [
            models.UniqueConstraint(
                name='Unique_ingredient_amount',
                fields=('recipe', 'ingredient')),
        ]

    def __str__(self):
        """Отображение модели."""
        return f'{self.recipe} - {self.ingredient}({self.amount})'


class BaseRecipeRelation(models.Model):
    """Абстрактная модель для связи рецепта с пользователем."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Пользователь'
    )

    class Meta:
        """Свойства."""

        abstract = True
        constraints = [
            models.UniqueConstraint(
                name='Unique_%(class)s_relation',
                fields=('recipe', 'user')
            ),
        ]

    def __str__(self):
        """Отображение модели."""
        return f'{self.user} - {self.recipe}'


class FavoriteRecipe(BaseRecipeRelation):
    """Модель для избранных рецептов."""

    class Meta(BaseRecipeRelation.Meta):
        """Свойства."""

        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(BaseRecipeRelation):
    """Модель для списка покупок."""

    class Meta(BaseRecipeRelation.Meta):
        """Свойства."""

        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'

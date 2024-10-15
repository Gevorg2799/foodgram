"""Модели приложение рецепты."""

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64)

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
        max_length=32
    )
    slug = models.SlugField(
        'Слаг тега',
        max_length=32,
        unique=True
    )

    class Meta:
        """Свойства."""

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        """Отображение модели."""
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    name = models.CharField(
        'Название',
        max_length=256
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
            )],
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
        ordering = ('-id',)

    def __str__(self):
        """Отображение модели."""
        return self.name


class MyFavoriteRecipe(models.Model):
    """Модель для избранных рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Автор'
    )

    class Meta:
        """Свойства."""

        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                name='Unique_favorite_recipe',
                fields=('recipe', 'author')),
        ]

    def __str__(self):
        """Отображение модели."""
        return f'{self.author} - {self.recipe}'


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


class ShoppingCart(models.Model):
    """Модель для списка покупок."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Карточка покупок'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Автор'
    )

    class Meta:
        """Свойства."""

        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = [
            models.UniqueConstraint(
                name='Unique_shopping_cart',
                fields=('recipe', 'user')),
        ]

    def __str__(self):
        """Отображение модели."""
        return f'{self.user}: {self.recipe}'

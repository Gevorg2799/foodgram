"""Сериализаторы для всех моделей."""
from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .fields import Base64ImageField
from recipes.models import (FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import SubscrUser


User = get_user_model()


class ReadUserSerializer(UserSerializer):
    """Сериализатор для получения юзера."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Свойства."""

        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Получаем отметку подписки."""
        return bool(
            self.context.get('request')
            and self.context['request'].user.is_authenticated
            and obj.authors.filter(
                author=self.context['request'].user).exists()
        )


class AvatarchangeSerializer(serializers.ModelSerializer):
    """Сериализатор для изсенения аватарки юзера."""

    avatar = Base64ImageField(required=True)

    class Meta:
        """Свойства."""

        model = User
        fields = ('avatar',)


class RecipeForSubscrSerializer(serializers.ModelSerializer):
    """Отображение рецепта в подписках."""

    image = Base64ImageField()

    class Meta:
        """Свойства."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscrUserSerializer(ReadUserSerializer):
    """Работа с подписками."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        """Свойства."""

        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count', 'avatar',
        )

    def get_recipes(self, obj):
        """Получение рецепта(recipes)."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                limit = int(recipes_limit)
                recipes = obj.recipes.all()[:limit]
            except ValueError:
                recipes = obj.recipes.all()
        else:
            recipes = obj.recipes.all()

        return RecipeForSubscrSerializer(recipes, many=True,
                                         context=self.context).data

    def get_recipes_count(self, obj):
        """Получение количества рецепта(recipes_count)."""
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/удаления подписки."""

    class Meta:
        """Свойства."""

        model = SubscrUser
        fields = ('subscriber', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=SubscrUser.objects.all(),
                fields=('subscriber', 'author'),
                message='Вы уже подписаны на этого пользователя.'
            )
        ]

    def validate(self, data):
        """Валидация на подписку на самого себя и уникальность подписки."""
        subscriber = data['subscriber']
        author = data['author']

        if subscriber == author:
            raise serializers.ValidationError(
                {'error': 'Вы не можете подписаться на самого себя.'}
            )

        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""

    class Meta:
        """Свойства."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Свойства."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Этот сериализатор будет включен в сериализатор рецепта.

    Для отображения количества ингредиентов в конкретном рецепте
    """

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        """Свойства."""

        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Получение карточки рецепта."""

    author = ReadUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredients_amout', many=True, read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Свойства."""

        model = Recipe
        fields = ('id', 'name', 'text', 'cooking_time',
                  'author', 'tags', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'image')

    def get_is_favorited(self, obj):
        """Получение поля (is_favorited)."""
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and obj.favoriterecipe.filter(
                user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Получение поля (is_in_shopping_cart)."""
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and obj.shoppingcart.filter(
                user=request.user, recipe=obj).exists()
        )


class IngredientRecipewriteSerializer(serializers.ModelSerializer):
    """Ингредиенты в рецепте при создании рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())

    class Meta:
        """Свойства."""

        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и изменения рецепта."""

    ingredients = IngredientRecipewriteSerializer(
        many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()

    class Meta:
        """Свойства."""

        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        """Общая валидация данных."""
        ingredients = data.get('ingredients')
        if ingredients is None:
            raise serializers.ValidationError(
                'Поле Ингредиенты обязательно для заполнения.')
        tags = data.get('tags')
        if tags is None:
            raise serializers.ValidationError(
                'Поле Теги обязательно для заполнения.')
        return data

    def validate_ingredients(self, value):
        """Проверка ингредиентов в рецепте."""
        ingredient_ids = [ingredient['id'] for ingredient in value]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')
        if not value:
            raise serializers.ValidationError(
                'Поле ингредиентов не может быть пустым.')
        return value

    def validate_tags(self, value):
        """Проверка тегов."""
        if not value:
            raise serializers.ValidationError(
                'Поле тегов не может быть пустым.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги должны быть уникальными.')

        return value

    def create_ingredients(self, recipe, ingredients_data):
        """Создаем ингредиенты для рецепта."""
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount')
            ) for ingredient in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта с указанием автора."""
        request = self.context.get('request')
        validated_data['author'] = request.user
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Приведение данных в нужный вид."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipeDetailSerializer(instance, context=context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        """Свойства."""

        model = FavoriteRecipe
        fields = ('recipe', 'user')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=('recipe', 'user'),
                message='Рецепт уже в избранном!'
            )
        ]

    def to_representation(self, instance):
        """Формирование ответа с краткой информацией о рецепте."""
        return RecipeForSubscrSerializer(instance.recipe,
                                         context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:

        model = ShoppingCart
        fields = ('recipe', 'user')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('recipe', 'user'),
                message='Рецепт уже в списке покупок!'
            )
        ]

    def to_representation(self, instance):
        """Формирование ответа с краткой информацией о рецепте."""
        return RecipeForSubscrSerializer(instance.recipe,
                                         context=self.context).data

"""Сериализаторы для всех моделей."""
import base64
import re

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from rest_framework import serializers
from users.models import MyUser, SubscrUser


class Base64ImageField(serializers.ImageField):
    """Сериализатор для работы с медиа."""

    def to_internal_value(self, data):
        """обработка полученных данных."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class ReadMyUserSerializer(UserSerializer):
    """Сериализатор для получения юзера."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Свойства."""

        model = MyUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Получаем отметку подписки."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.authors.filter(author=user).exists()


class CreateMyUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        """Свойства."""

        model = MyUser
        fields = ('id', 'email', 'first_name',
                  'last_name', 'password', 'username')

    def validate_username(self, value):
        """Проверка username.

        Соответствие регулярному выражению
        """
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Username может содержать только буквы, цифры и символы'
            )
        # if 'username' in value.lower() or 'me' in value.lower():
        #     raise serializers.ValidationError(
        #         'Имя пользователя не должен содержать слово username ил me.'
        #     )
        return value

    def validate_password(self, value):
        """Првоерка пароля."""
        if len(value) < 8:
            raise serializers.ValidationError(
                "Новый пароль должен содержать минимум 8 символов.")
        if re.search(r'[А-Яа-яЁё]', value):
            raise serializers.ValidationError(
                "Пароль не может содержать кириллицу."
            )
        if not re.match(r'^[A-Za-z0-9!@#$%^&*()_+=\[\]{};:,.<>?|`~\-]+$',
                        value):
            raise serializers.ValidationError(
                "Пароль может содержать только латинские буквы, "
                "цифры и специальные символы."
            )
        if 'password' in value.lower():
            raise serializers.ValidationError(
                'Пароль не должен содержать слово "password".'
            )

        return value


class AvatarchangeSerializer(serializers.ModelSerializer):
    """Сериализатор для изсенения аватарки юзера."""

    avatar = Base64ImageField()

    class Meta:
        """Свойства."""

        model = MyUser
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    """Изменение пароля юзером."""

    current_password = serializers.CharField(
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'}
    )

    def validate_current_password(self, value):
        """Првоерка введенного пароля."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверный.")
        return value

    def validate_new_password(self, value):
        """Проверка нового пароля."""
        if len(value) < 8:
            raise serializers.ValidationError(
                "Новый пароль должен содержать минимум 8 символов.")
        if re.search(r'[А-Яа-яЁё]', value):
            raise serializers.ValidationError(
                "Пароль не может содержать кириллицу."
            )
        if not re.match(r'^[A-Za-z0-9!@#$%^&*()_+=\[\]{};:,.<>?|`~\-]+$',
                        value):
            raise serializers.ValidationError(
                "Пароль может содержать только латинские буквы, "
                "цифры и специальные символы."
            )
        if 'password' in value.lower():
            raise serializers.ValidationError(
                'Пароль не должен содержать слово "password".'
            )

        return value

    def update(self, instance, validated_data):
        """Обновление пароля."""
        new_password = validated_data.get('new_password')
        instance.set_password(new_password)
        instance.save()
        return instance


class RecipeForSubscrSerializer(serializers.ModelSerializer):
    """Отображение рецепта в подписках."""

    image = image = Base64ImageField()

    class Meta:
        """Свойства."""

        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscrUserSerializer(serializers.ModelSerializer):
    """Работа с подписками."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        """Свойства."""

        model = MyUser
        fields = [
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count', 'avatar',
        ]

    def get_is_subscribed(self, obj):
        """Получение поля is_subscribed."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return SubscrUser.objects.filter(subscriber=user, author=obj).exists()

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

    id = serializers.PrimaryKeyRelatedField(
        source="ingredient.id", queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        """Свойства."""

        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Получение карточки рецепта."""

    author = ReadMyUserSerializer(read_only=True)
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
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorite.filter(author=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Получение поля (is_in_shopping_cart)."""
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.shopping_cart.filter(user=user, recipe=obj).exists()
        return False


class IngredientRecipewriteSerializer(serializers.ModelSerializer):
    """Ингредиенты в рецепте при создании рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        """Свойства."""

        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и изменения рецепта."""

    ingredients = IngredientRecipewriteSerializer(
        source='ingredients_amout', many=True)
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
        ingredients = data.get('ingredients_amout')
        if ingredients is None:
            raise serializers.ValidationError(
                'Поле Ингредиенты обязательно для заполнения.')
        tags = data.get('tags')
        if tags is None:
            raise serializers.ValidationError(
                'Поле Теги обязательно для заполнения.')
        self.validate_ingredients(ingredients)
        self.validate_tags(tags)
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
        for ingredient in value:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество каждого ингредиента должно быть не меньше 1.'
                )

        return value

    def validate_tags(self, value):
        """Проверка тегов."""
        if not value:
            raise serializers.ValidationError(
                'Поле тегов не может быть пустым.')
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
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

    def update_ingredients(self, instance, ingredients_data):
        """Обновляем ингредиенты рецепта."""
        existing_ingredients = IngredientRecipe.objects.filter(recipe=instance)
        existing_ingredients_dict = {
            ing.ingredient: ing for ing in existing_ingredients}
        new_ingredients = []

        for ingredient_data in ingredients_data:
            if not isinstance(ingredient_data, dict):
                raise ValueError(
                    "Ожидался словарь с данными ингредиента,"
                    f"получено: {ingredient_data}")

            ingredient = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            if ingredient in existing_ingredients_dict:
                existing_ingredient = existing_ingredients_dict[ingredient]
                if existing_ingredient.amount != amount:
                    existing_ingredient.amount = amount
                    existing_ingredient.save()
            else:
                IngredientRecipe.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data.get('id'),
                    amount=amount)

            new_ingredients.append(ingredient)
        existing_ingredients.exclude(
            ingredient__in=new_ingredients).delete()

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients_data = validated_data.pop('ingredients_amout', None)
        tags_data = validated_data.pop('tags', None)
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        if ingredients_data:
            self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients_data = validated_data.pop('ingredients_amout', None)
        tags_data = validated_data.pop('tags', None)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        if tags_data:
            instance.tags.set(tags_data)
        if ingredients_data:
            current_ingredients = [
                {'ingredient': ing.ingredient, 'amount': ing.amount}
                for ing in instance.ingredients_amout.all()
            ]
            if current_ingredients != ingredients_data:
                self.update_ingredients(instance, ingredients_data)

        instance.save()
        return instance

    def to_representation(self, instance):
        """Приведение данных в нужный вид."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipeDetailSerializer(instance, context=context).data

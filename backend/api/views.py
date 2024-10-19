import io

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_encode
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarchangeSerializer, FavoriteSerializer,
                          IngredientSerializer, ReadUserSerializer,
                          RecipeCreateUpdateSerializer, RecipeDetailSerializer,
                          RecipeForSubscrSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, SubscrUserSerializer,
                          TagSerializer)
from recipes.models import (FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import SubscrUser, User


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов (только чтение)."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов (только чтение)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class UserViewset(UserViewSet):
    """ViewSet для работы с юзером."""

    queryset = User.objects.all()
    http_method_names = ('get', 'post', 'put', 'patch', 'delete',)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me',
        url_name='me',
    )
    def me(self, request):
        """Возвращает данные текущего юзера."""
        serializer = ReadUserSerializer(
            request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='avatar',
    )
    def new_avatar(self, request):
        """Изменение аватарки юзера."""
        instance = self.get_instance()
        serializer = AvatarchangeSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @new_avatar.mapping.delete
    def avatar_remove(self, request):
        """Удаление аватарки пользователя."""
        instance = self.get_instance()
        if instance.avatar:
            instance.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар не установлен.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def get_instance(self):
        """Возвращает текущего пользователя."""
        return self.request.user

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            )
    def subscriptions(self, request):
        """Возвращает список пользовательна кого подписан."""
        user = request.user
        authors = User.objects.filter(
            authors__subscriber=user).prefetch_related(
            'recipes__ingredients_amout__ingredient')
        page = self.paginate_queryset(authors)
        serializer = SubscrUserSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'],
            url_path='(?P<pk>[^/.]+)/subscribe',
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписаться на пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=pk)
        data = {'subscriber': user.id, 'author': author.id}
        serializer = SubscriptionSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscrUserSerializer(author, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Отписаться от пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=pk)
        deleted_count, _ = SubscrUser.objects.filter(
            subscriber=user, author=author).delete()
        if deleted_count == 0:
            return Response(
                {'error': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        """Распределение сериализатора в зависимости от метода."""
        if self.request.method == 'GET':
            return RecipeDetailSerializer
        return RecipeCreateUpdateSerializer

    def generate_shopping_list_file(self, request):
        """Генерация файла со списком покупок."""
        ingredients_summary = (
            IngredientRecipe.objects
            .filter(recipe__shoppingcart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        shopping_list_content = "Ваш список покупок:\n\n"
        for ingredient in ingredients_summary:
            name = ingredient['ingredient__name']
            amount = ingredient['total_amount']
            measurement_unit = ingredient['ingredient__measurement_unit']
            shopping_list_content += (
                f"• {name} — {amount} ({measurement_unit})\n"
            )

        shopping_list_bytes = shopping_list_content.encode('utf-8')
        shopping_list_file = io.BytesIO(shopping_list_bytes)
        response = FileResponse(
            shopping_list_file, as_attachment=True, content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"')
        return response

    def add_recipe_relation(self, request, pk, serializer_class):
        """Добавление записи в избранное или список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'recipe': recipe.id, 'user': request.user.id}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeForSubscrSerializer(
                recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def remove_recipe_relation(self, request, pk, model):
        """Удаление записи из избранного или списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        instance = model.objects.filter(recipe=recipe, user=request.user)
        deleted_count, _ = instance.delete()

        if deleted_count == 0:
            return Response({'error': 'Рецепт не найден!'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': 'Рецепт удалён!'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        if request.method == 'POST':
            return self.add_recipe_relation(request, pk, FavoriteSerializer)
        return self.remove_recipe_relation(request, pk, FavoriteRecipe)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавление или удаление рецепта из списка покупок."""
        if request.method == 'POST':
            return self.add_recipe_relation(request, pk,
                                            ShoppingCartSerializer)
        return self.remove_recipe_relation(request, pk, ShoppingCart)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Генерация короткой ссылки для рецепта."""
        recipe = self.get_object()
        short_code = urlsafe_base64_encode(str(recipe.id).encode('utf-8'))
        short_path = f"/s/{short_code}/"
        short_link = request.build_absolute_uri(short_path)
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в формате txt."""
        return self.generate_shopping_list_file(request)

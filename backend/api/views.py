"""Views-классы."""
import io
from collections import defaultdict

from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Ingredient, MyFavoriteRecipe, Recipe, ShoppingCart,
                            Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import MyUser, SubscrUser

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarchangeSerializer, CreateMyUserSerializer,
                          IngredientSerializer, ReadMyUserSerializer,
                          RecipeCreateUpdateSerializer, RecipeDetailSerializer,
                          RecipeForSubscrSerializer, SetPasswordSerializer,
                          SubscrUserSerializer, TagSerializer)

# Create your views here.


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

    queryset = MyUser.objects.all()
    http_method_names = ('get', 'post', 'put', 'patch', 'delete',)

    def get_serializer_class(self):
        """Распределение сериализатора в зависимости от метода."""
        if self.request.method == 'GET':
            return ReadMyUserSerializer
        return CreateMyUserSerializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me',
        url_name='me',
    )
    def me(self, request):
        """Возвращает данные текущего юзера."""
        serializer = ReadMyUserSerializer(
            request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='avatar',
    )
    def avatar(self, request):
        """Метод для работы с аватаркой юзера."""
        if request.method == 'PUT':
            return self.new_avatar(request)
        elif request.method == 'DELETE':
            return self.avatar_remove()

    def new_avatar(self, request):
        """Изменение аватарки юзера."""
        if 'avatar' not in request.data:
            return Response(
                {'avatar': 'Это поле обязательно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем экземпляр пользователя
        instance = self.get_instance()
        # Создаём экземпляр сериализатора с данными
        serializer = AvatarchangeSerializer(instance, data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def avatar_remove(self):
        """Удаление аватарки пользователя."""
        instance = self.get_instance()
        if instance.avatar:
            instance.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар не установлен.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        url_name='set password',
        permission_classes=[IsAuthenticated],
    )
    def set_password(self, request):
        """Изменение пароля юзера."""
        user = request.user  # Получаем текущего пользователя
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request})

        # Проверяем валидность введенных данных
        if serializer.is_valid():
            # Если данные валидны, обновляем пароль
            serializer.update(user, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # В случае ошибки возвращаем сообщение с ошибками валидации
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_instance(self):
        """Возвращает текущего пользователя."""
        return self.request.user

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            # url_path='subscriptions'
            )
    def subscriptions(self, request):
        """Возвращает список пользовательна кого подписан."""
        user = request.user
        authors = MyUser.objects.filter(
            authors__subscriber=user).prefetch_related(
            'recipes__ingredients_amout__ingredient')
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscrUserSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = SubscrUserSerializer(
            authors, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            url_path='(?P<pk>[^/.]+)/subscribe')
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться на пользователя."""
        user = request.user
        author = get_object_or_404(MyUser, pk=pk)

        if author == user:
            return Response(
                {'error': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if SubscrUser.objects.filter(subscriber=user,
                                         author=author).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            SubscrUser.objects.create(subscriber=user, author=author)
            serializer = SubscrUserSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = SubscrUser.objects.filter(
                subscriber=user, author=author)
            if not subscription.exists():
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter  # Указание класса фильтрации

    def get_serializer_class(self):
        """Распределение сериализатора в зависимости от метода."""
        if self.request.method == 'GET':
            return RecipeDetailSerializer
        return RecipeCreateUpdateSerializer

    def get_permissions(self):
        """Распределение раазрешений."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthorOrReadOnly]
        elif self.action in ['create', 'favorite', 'shopping_cart',
                             'download_shopping_cart']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        """При создании рецепта сохраняем его с текущим автором."""
        print("Выполняем создание с данными:", serializer.validated_data)
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """Обновление рецепта только автором."""
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Удаление рецепта только автором."""
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'error': 'Вы не можете удалять этот рецепт!'},
                status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if MyFavoriteRecipe.objects.filter(recipe=recipe,
                                               author=request.user).exists():
                return Response({'error': 'Рецепт уже в избранном!'},
                                status=status.HTTP_400_BAD_REQUEST)
            MyFavoriteRecipe.objects.create(recipe=recipe, author=request.user)
            serializer = RecipeForSubscrSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            favorite = MyFavoriteRecipe.objects.filter(
                recipe=recipe, author=request.user)
            if favorite.exists():
                favorite.delete()
                return Response({'success': 'Рецепт удалён из избранного!'},
                                status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Рецепт не найден в избранном!'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавление или удаление рецепта из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(recipe=recipe,
                                           user=request.user).exists():
                return Response({'error': 'Рецепт уже в списке покупок!'},
                                status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=request.user)
            serializer = RecipeForSubscrSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(
                recipe=recipe, user=request.user)
            if cart_item.exists():
                cart_item.delete()
                return Response(
                    {'success': 'Рецепт удалён из списка покупок!'},
                    status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Рецепт не найден в списке покупок!'},
                            status=status.HTTP_400_BAD_REQUEST)

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
        """Скачивание списка покупок в формате .txt."""
        # Словарь для хранения ингредиентов и их суммарного количества
        ingredients_summary = defaultdict(int)

        # Получаем все рецепты в списке покупок текущего пользователя
        cart_items = ShoppingCart.objects.filter(
            user=request.user).select_related(
            'recipe').prefetch_related('recipe__ingredients_amout__ingredient')

        for item in cart_items:
            recipe = item.recipe
            # Итерируем по ингредиентам в рецепте и суммируем их количество
            for ingred_rec in recipe.ingredients_amout.all():
                ingredients_summary[ingred_rec.ingredient] += ingred_rec.amount

        # Создаем текстовый контент с суммарными ингредиентами
        shopping_list_content = "Ваш список покупок:\n\n"
        for ingredient, amount in ingredients_summary.items():
            shopping_list_content += (
                f"• {ingredient.name} — "
                f"{amount}({ingredient.measurement_unit})\n")

        # Кодируем строку в байты
        shopping_list_bytes = shopping_list_content.encode('utf-8')

        # Создаем BytesIO объект
        shopping_list_file = io.BytesIO(shopping_list_bytes)

        # Создаём FileResponse с правильным типом контента
        response = FileResponse(shopping_list_file, as_attachment=True,
                                content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )

        return response


class ShortLinkRedirectView(View):
    """Для редиректа короткой ссылки."""

    def get(self, request, short_code, *args, **kwargs):
        """Получение URL и редирект."""
        recipe_id = urlsafe_base64_decode(short_code).decode('utf-8')
        recipe = get_object_or_404(Recipe, id=int(recipe_id))
        recipe_url = request.build_absolute_uri(f"/recipes/{recipe.id}/")
        return redirect(recipe_url)


class FavoriteRecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления избранными рецептами."""

    queryset = MyFavoriteRecipe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получение данных."""
        return MyFavoriteRecipe.objects.filter(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в избранные."""
        recipe_id = request.data.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if MyFavoriteRecipe.objects.filter(recipe=recipe,
                                           author=request.user).exists():
            return Response({'error': 'Рецепт уже в избранном!'},
                            status=status.HTTP_400_BAD_REQUEST)
        MyFavoriteRecipe.objects.create(recipe=recipe, author=request.user)
        return Response({'success': 'Рецепт добавлен в избранное!'},
                        status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Удаление рецепта из списка избранных."""
        recipe_id = self.kwargs.get('pk')
        favorite = MyFavoriteRecipe.objects.filter(
            recipe__id=recipe_id, author=request.user)
        if favorite.exists():
            favorite.delete()
            return Response({'success': 'Рецепт удалён из избранного!'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Рецепт не найден в избранном!'},
                        status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """ViewSet для управления списком покупок."""

    queryset = ShoppingCart.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получение данных."""
        return ShoppingCart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в списк покупок."""
        recipe_id = request.data.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if ShoppingCart.objects.filter(recipe=recipe,
                                       user=request.user).exists():
            return Response({'error': 'Рецепт уже в корзине!'},
                            status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.create(recipe=recipe, user=request.user)
        return Response({'success': 'Рецепт добавлен в список покупок!'},
                        status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Удаление рецепта из списка покупок."""
        recipe_id = self.kwargs.get('pk')
        cart_item = ShoppingCart.objects.filter(
            recipe__id=recipe_id, user=request.user)
        if cart_item.exists():
            cart_item.delete()
            return Response({'success': 'Рецепт удалён из списка покупок!'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Рецепт не найден в списке покупок!'},
                        status=status.HTTP_400_BAD_REQUEST)

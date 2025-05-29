"""View-классы для обработки запросов API приложения recipes."""

from django.db.models import Sum, Count
from django.http import FileResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from django.shortcuts import get_object_or_404, reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny
)
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
    generate_hash,
)
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    RecipeCreateSerializer,
    RecipeSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    SubscriptionListSerializer,
    SubscriptionSerializer,
    TagSerializer,
    IngredientSerializer,
    UserSerializer
)
from .filters import IngredientFilter, RecipeFilterSet


class UserViewSet(DjoserUserViewSet):
    """ViewSet для работы с пользователями и подписками."""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=('get',))
    def me(self, request):
        """Получение данных текущего пользователя."""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False, methods=('get',), permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Список подписок с пагинацией."""
        authors = User.objects.filter(
            following__user=request.user
        ).annotate(
            recipes_count=Count('recipes')
        ).prefetch_related('recipes').order_by('username')

        page = self.paginate_queryset(authors)
        serializer = SubscriptionListSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionSerializer,
    )
    def subscribe(self, request, id=None):
        """Подписка на автора."""
        author = get_object_or_404(User, pk=id)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписка от автора."""
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author_id=id
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT if deleted
            else status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=('put',),
        detail=False,
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
        serializer_class=UserSerializer
    )
    def avatar(self, request):
        """Обновление аватара текущего пользователя."""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара текущего пользователя."""
        user = request.user
        if user.avatar.delete():
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами (только чтение)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами (только чтение)."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.prefetch_related(
        'tags', 'ingredients').select_related('author')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_serializer_class(self):
        """Возвращает класс сериализатора в зависимости от действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Создает рецепт с текущим пользователем в качестве автора."""
        serializer.save(author=self.request.user)

    def _handle_favorite_shopping_action(self, serializer_class, request, pk):
        """Общий метод для добавления в избранное/корзину."""
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = serializer_class(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _handle_favorite_shopping_delete(self, model, request, pk):
        """Общий метод для удаления из избранного/корзины."""
        deleted = model.objects.filter(
            user=request.user,
            recipe_id=pk
        ).delete()[0]
        return Response(
            status=status.HTTP_204_NO_CONTENT if deleted
            else status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        serializer_class=FavoriteSerializer
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        return self._handle_favorite_shopping_action(
            FavoriteSerializer, request, pk
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        return self._handle_favorite_shopping_delete(
            Favorite, request, pk
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        serializer_class=ShoppingCartSerializer
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в корзину."""
        return self._handle_favorite_shopping_action(
            ShoppingCartSerializer, request, pk
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаление рецепта из корзины."""
        return self._handle_favorite_shopping_delete(
            ShoppingCart, request, pk
        )

    @action(detail=False, methods=('get',), permission_classes=(
            IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Скачивает список покупок в виде текстового файла."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')

        shopping_list = [
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) - "
            f"{item['total_amount']}"
            for item in ingredients
        ]

        response = FileResponse(
            '\n'.join(shopping_list), content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response

    @action(
        methods=('get',),
        detail=True,
        url_path='get-link',
        url_name='get-link'
    )
    def get_link(self, request, pk=None):
        """Генерирует короткую ссылку на рецепт."""
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = generate_hash()
            recipe.save()
        short_link_url = reverse(
            'recipe-by-short-link', kwargs={'short_link': recipe.short_link}
        )
        return Response({
            'short-link': request.build_absolute_uri(short_link_url)
        })

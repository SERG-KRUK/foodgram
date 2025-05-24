"""View-классы для обработки запросов API приложения recipes."""

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

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
    IngredientSerializer,
    PasswordSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all()
    parser_classes = [JSONParser]

    def get_serializer_class(self):
        """Возвращает класс сериализатора в зависимости от действия."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """Возвращает классы разрешений в зависимости от действия."""
        if self.action in ['create', 'retrieve', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получение данных текущего пользователя."""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        user = request.user
        queryset = Subscription.objects.filter(user=user).select_related(
            'author')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit')
                }
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset,
            many=True,
            context={
                'request': request,
                'recipes_limit': request.query_params.get('recipes_limit')
            }
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        """Изменение пароля текущего пользователя."""
        user = request.user
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.data.get('current_password')
            if not user.check_password(current_password):
                return Response(
                    {'current_password': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка/отписка на автора."""
        author = get_object_or_404(User, id=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'You cannot subscribe to yourself'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'error': 'You are already subscribed to this author'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(
                user=user, author=author)
            serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription,
                user=user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        """Обновление или удаление аватара текущего пользователя."""
        user = request.user
        if request.method == "PUT":
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == "DELETE":
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_ingredients(request):
    """Получение списка всех ингредиентов."""
    ingredients = Ingredient.objects.all().values(
        'id', 'name', 'measurement_unit')
    return Response(list(ingredients))


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами (только чтение)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами (только чтение)."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        """Фильтрация ингредиентов по имени."""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        """Фильтрация рецептов по различным параметрам."""
        queryset = super().get_queryset()
        user = self.request.user

        # Фильтр по автору
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author__id=author_id)

        # Фильтр по тегам
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        # Фильтр по корзине покупок
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart and user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=user)

        # Фильтр по избранному
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited and user.is_authenticated:
            queryset = queryset.filter(favorites__user=user)

        return queryset

    def get_serializer_class(self):
        """Возвращает класс сериализатора в зависимости от действия."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Создание рецепта с указанием текущего пользователя как автора."""
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        """Добавление request в контекст сериализатора."""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def handle_exception(self, exc):
        """функция валидатор ингридиентов."""
        if isinstance(exc, serializers.ValidationError):
            response_data = {}
            if 'ingredients' in exc.detail:
                response_data['ingredients'] = exc.detail['ingredients']
            if 'non_field_errors' in exc.detail:
                response_data['non_field_errors'] = exc.detail[
                    'non_field_errors']
            if response_data:
                return Response(
                    response_data,
                    status=status.HTTP_400_BAD_REQUEST
                )
        return super().handle_exception(exc)

    @action(
        detail=True,
        methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            cart_item = get_object_or_404(
                ShoppingCart, user=user, recipe=recipe)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'])
    def shopping_cart_list(self, request):
        """Получение списка рецептов в корзине покупок."""
        recipes = Recipe.objects.filter(shopping_cart__user=request.user)
        serializer = ShortRecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в виде текстового файла."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        shopping_list = []
        for item in ingredients:
            shopping_list.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) - "
                f"{item['total_amount']}"
            )

        response = HttpResponse(
            '\n'.join(shopping_list), content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        methods=['get'],
        detail=True, url_path='get-link', url_name='get-link')
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = generate_hash()
            recipe.save()
        return Response({
            'short-link': request.build_absolute_uri(
                f'/s/{recipe.short_link}/')
        })


def recipe_by_short_link(request, short_link):
    """Перенаправление по короткой ссылке на полный URL рецепта."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f'/recipes/{recipe.pk}/')


class RecipeDetailView(APIView):
    """APIView для получения детальной информации о рецепте."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Получение детальной информации о рецепте."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data)

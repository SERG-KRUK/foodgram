from rest_framework import viewsets, status
from rest_framework.reverse import reverse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated, AllowAny,
                                        IsAuthenticatedOrReadOnly)
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view
from django.db.models import Sum
from django.views.decorators.http import require_GET
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from .models import (User, Recipe, RecipeIngredient, Tag, Ingredient,
                     Favorite, ShoppingCart, Subscription, LinkMapped,
                     generate_hash)
from .serializers import (PasswordSerializer, UserCreateSerializer,
                          UserSerializer, TagSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeCreateSerializer,
                          ShortRecipeSerializer, SubscriptionSerializer,
                          ShortenerSerializer, ShortLinkSerializer)
from .permissions import IsAuthorOrReadOnly, IsAdmin


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    parser_classes = [JSONParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'retrieve', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя"""
        user = request.user
        queryset = Subscription.objects.filter(
            user=user).select_related('author')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request, 'recipes_limit':
                         request.query_params.get('recipes_limit')}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset,
            many=True,
            context={'request': request, 'recipes_limit':
                     request.query_params.get('recipes_limit')}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
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

    @action(detail=True,
            methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
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
    ingredients = Ingredient.objects.all().values(
        'id', 'name', 'measurement_unit')
    return Response(list(ingredients))


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Фильтр по автору
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author__id=author_id)

        # Остальные фильтры (теги, корзина, избранное) остаются без изменений
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart and user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=user)

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited and user.is_authenticated:
            queryset = queryset.filter(favorites__user=user)

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
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
        recipes = Recipe.objects.filter(shopping_cart__user=request.user)
        serializer = ShortRecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
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
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = generate_hash()
            recipe.save()
        return Response({
            'short-link': request.build_absolute_uri(f'/s/{recipe.short_link}/')
        })


def recipe_by_short_link(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f'/recipes/{recipe.pk}/')


class RecipeDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data)


class AdminTagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdmin]
    pagination_class = None


class AdminIngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdmin]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset

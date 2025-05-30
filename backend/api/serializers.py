"""Сериализаторы для проекта."""

from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
    ShoppingCart,
    Favorite,
)
from .constants import MIN_VALUE, RECIPE_COUNT


User = get_user_model()


class UserSerializer(BaseUserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(BaseUserSerializer.Meta):
        """Мета класс для пользователя."""

        fields = BaseUserSerializer.Meta.fields + (
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Метод для подписок."""
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.subscriptions_to_author.filter(
                    user=request.user).exists())


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Мета класс для тегов."""

        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        """Мета класс для ингридиентов."""

        model = Ingredient
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингридиентов."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        """Мета класс для рецептов."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингридиентов."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_VALUE)

    class Meta:
        """Мета класс для рецептов."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор детальной страницы рецепта."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    author = UserSerializer()
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipe_ingredients'
    )

    class Meta:
        """Мета класс для рецептов."""

        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        """Метод для избранного."""
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.favorite_set.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, obj):
        """Метод для корзины покупок."""
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.shoppingcart_set.filter(user=request.user).exists())


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для связей пользователь-рецепт."""
    
    def validate(self, data):
        """Проверяет, что рецепт еще не добавлен."""
        if self.Meta.model.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            verbose_name = self.Meta.model._meta.verbose_name
            raise serializers.ValidationError(
                f'Рецепт уже в {verbose_name}'
            )
        return data
    
    def to_representation(self, instance):
        """Преобразует объект в словарь для ответа API."""
        request = self.context.get('request')
        context = {'request': request}
        return ShortRecipeSerializer(instance.recipe, context=context).data


class FavoriteSerializer(BaseUserRecipeSerializer):
    """Сериализатор для избранного."""

    class Meta:
        """Мета класс."""

        model = Favorite
        fields = ('user', 'recipe')
        verbose_name = 'избранном'


class ShoppingCartSerializer(BaseUserRecipeSerializer):
    """Сериализатор для корзины покупок."""

    class Meta:
        """Мета класс."""

        model = ShoppingCart
        fields = ('user', 'recipe')
        verbose_name = 'корзине'


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientWriteSerializer(many=True, required=False)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_VALUE)

    class Meta:
        """Мета класс для создания рецептов."""

        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    @transaction.atomic
    def create(self, validated_data):
        """Метод создания рецепта."""
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        validated_data.pop('author', None)

        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Метод редактирования рецепта."""
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    @staticmethod
    def _create_ingredients(recipe, ingredients_data):
        """Метод для ингридиентов рецепта."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

    def validate_tags(self, value):
        """Метод валидации тегов рецепта."""
        if not value:
            raise serializers.ValidationError('Необходим хотя бы один тег.')

        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')

        return value

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        ingredient_ids = [ingredient['id'] for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными'
            )
        return value

    def to_representation(self, instance):
        """Метод для рецептов."""
        return RecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецепта."""

    class Meta:
        """Мета класс."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписок."""

    class Meta:
        """Мета класс для подписок."""

        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        """Валидация подписки."""
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        if Subscription.objects.filter(
                user=data['user'], author=data['author']).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора'
            )

        return data

    def to_representation(self, instance):
        """Репрезентация после подписки."""
        return SubscriptionListSerializer(
            instance.author, context=self.context
        ).data


class SubscriptionListSerializer(UserSerializer):
    """Сериализатор для вывода подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True, default=RECIPE_COUNT
    )

    class Meta(UserSerializer.Meta):
        """Мета класс для подписок."""

        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Метод вывода подписок."""
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

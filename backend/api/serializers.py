"""Serializers for recipes application."""

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
)


User = get_user_model()


class UserSerializer(BaseUserSerializer):
    """Serializer for user details with additional fields."""
    
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + (
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.following.filter(user=request.user).exists())


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Serializer for reading recipe ingredients."""
    
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Serializer for writing recipe ingredients."""
    
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe details."""
    
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
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.favorite_set.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.shoppingcart_set.filter(user=request.user).exists())


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer for recipe creation/update."""
    
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        instance = super().update(instance, validated_data)

        if tags is not None:
            instance.tags.set(tags)
        
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(instance, ingredients_data)

        return instance

    @staticmethod
    def _create_ingredients(recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Необходим хотя бы один тег.')
        
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
            
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходим хотя бы один ингредиент.'
            )
        
        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
            
        return value

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Short serializer for recipes."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписок."""
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Subscription
        fields = ('author',)
        extra_kwargs = {
            'user': {'read_only': True},
        }

    def validate(self, data):
        request = self.context.get('request')
        author = data['author']
        
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Требуется аутентификация")
            
        if request.user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя")
            
        if Subscription.objects.filter(
                user=request.user, author=author).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого автора")
            
        return data

    def to_representation(self, instance):
        return SubscriptionListSerializer(
            instance.author,
            context=self.context
        ).data


class SubscriptionListSerializer(UserSerializer):
    """Сериализатор для вывода подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
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

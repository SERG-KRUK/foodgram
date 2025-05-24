"""Serializers for recipes application."""
import base64
import uuid
from collections import Counter

from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
)
from rest_framework import serializers

from .error import Error
from recipes.models import (
    Ingredient,
    LinkMapped,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
)


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Custom image field for base64 encoded images."""

    def to_internal_value(self, data):
        """Convert base64 image data to Django ContentFile."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"{uuid.uuid4()}.{ext}"
            )
        return super().to_internal_value(data)


class PasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class UserCreateSerializer(BaseUserCreateSerializer):
    """Serializer for user creation."""

    class Meta(BaseUserCreateSerializer.Meta):
        """Meta class for UserCreateSerializer."""

        model = User
        fields = ['email', 'username', 'password', 'first_name', 'last_name']


class UserSerializer(BaseUserSerializer):
    """Serializer for user details."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(BaseUserSerializer.Meta):
        """Meta class for UserSerializer."""

        model = User
        fields = [
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed', 'avatar'
        ]

    def get_avatar(self, obj):
        """Get absolute URL for avatar."""
        if not obj.avatar:
            return None

        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url

    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        """Meta class for TagSerializer."""

        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        """Meta class for IngredientSerializer."""

        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for recipe ingredients."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        """Meta class for RecipeIngredientSerializer."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe details."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    short_link = serializers.CharField(read_only=True)

    class Meta:
        """Meta class for RecipeSerializer."""

        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart', 'short_link'
        ]

    def get_image(self, obj):
        """Get absolute URL for recipe image."""
        if not obj.image:
            return None
        return obj.image.url

    def get_is_favorited(self, obj):
        """Check if recipe is favorited by current user."""
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Check if recipe is in shopping cart of current user."""
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.shopping_cart.filter(user=user).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer for recipe creation."""

    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Tag.objects.all(),
        ),
        allow_empty=False,
        required=True,
    )
    ingredients = serializers.ListField(
        child=RecipeIngredientSerializer(),
        allow_empty=False,
        required=True,
    )
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    @staticmethod
    def _check_duplicates(array, field_name):
        counts = Counter(array)
        duplicates = {item for item, count in counts.items() if count > 1}
        if duplicates:
            raise serializers.ValidationError(
                {field_name: Error.DUPLICATES.format(duplicates)}
            )

    def validate_tags(self, tags):
        self._check_duplicates([tag.id for tag in tags], 'tags')
        return tags

    def validate_ingredients(self, ingredients):
        self._check_duplicates(
            [item['ingredient'].id for item in ingredients],
            'ingredients',
        )
        return ingredients

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(Error.NO_IMAGE)
        return image

    @staticmethod
    def _save_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        try:
            new_ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            self._save_ingredients(recipe, new_ingredients)
        except KeyError:
            pass
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        return RecipeSerializer(recipe, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Short serializer for recipes."""

    class Meta:
        """Meta class for ShortRecipeSerializer."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShortLinkSerializer(serializers.Serializer):
    """Serializer for short links."""

    short_link = serializers.URLField()


class ShortenerSerializer(serializers.ModelSerializer):
    """Serializer for link shortening."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        """Meta class for ShortenerSerializer."""

        model = LinkMapped
        fields = ('short_link',)

    def get_short_link(self, obj):
        """Get absolute URL for short link."""
        request = self.context.get('request')
        return request.build_absolute_uri(
            f"/s/{obj.url_hash}/"
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscriptions."""

    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """Meta class for SubscriptionSerializer."""

        model = Subscription
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_is_subscribed(self, obj):
        """Check if subscription exists."""
        return True

    def get_recipes_count(self, obj):
        """Get count of author's recipes."""
        return obj.author.recipes.count()

    def get_recipes(self, obj):
        """Get author's recipes."""
        recipes = obj.author.recipes.all()
        limit = self.context.get('recipes_limit')
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(recipes, many=True).data

    def get_avatar(self, obj):
        """Get absolute URL for avatar."""
        if obj.author.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.author.avatar.url)
            return obj.author.avatar.url
        return None

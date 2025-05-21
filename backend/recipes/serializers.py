from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer

from foodgram import settings
from .models import (Recipe, RecipeIngredient, Tag, Ingredient,
                     Subscription, LinkMapped)
from django.core.files.base import ContentFile
import base64
import uuid


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"{uuid.uuid4()}.{ext}"
            )
        return super().to_internal_value(data)


class PasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ['email', 'username', 'password', 'first_name', 'last_name']


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ['email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed', 'avatar']

    def get_avatar(self, obj):
        if not obj.avatar:
            return None

        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
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
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart', 'short_link'
        ]

    def get_image(self, obj):
        if not obj.image:
            return None
        return obj.image.url

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.shopping_cart.filter(user=user).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data.pop('author', None)
        tags = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])

        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )

        recipe.tags.set(tags)
        self._create_or_update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_or_update_ingredients(instance, ingredients_data)

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        """Создает или обновляет ингредиенты рецепта"""
        ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredients)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходим хотя бы один ингредиент.")

        # Проверка уникальности ингредиентов
        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться.")

        # Проверка количества
        for ingredient in value:
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError(
                    f"Количество ингредиента '{ingredient['id'].name}' "
                    "должно быть больше 0"
                )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Необходим хотя бы один тег.")
        return value

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Время приготовления должно быть больше 0.")
        return value

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShortLinkSerializer(serializers.Serializer):
    short_link = serializers.URLField()


class ShortenerSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = LinkMapped
        fields = ('short_link',)

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            f"/s/{obj.url_hash}/"
        )


class SubscriptionSerializer(serializers.ModelSerializer):
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
        model = Subscription
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_is_subscribed(self, obj):
        return True  # Так как это подписка, всегда True

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_recipes(self, obj):
        recipes = obj.author.recipes.all()
        limit = self.context.get('recipes_limit')
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(recipes, many=True).data

    def get_avatar(self, obj):
        if obj.author.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.author.avatar.url)
            return obj.author.avatar.url
        return None

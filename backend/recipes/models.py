"""Модели пользователи, ингредиенты, рецепты и связанные сущности."""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import string
from random import choice, randint


class User(AbstractUser):
    """Модель пользователя с расширенными полями."""

    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        """Мета-класс для модели User."""
        
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Tag(models.Model):
    """Модель тега для рецептов."""

    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True, allow_unicode=True)

    def __str__(self):
        """Возвращает строковое представление тега."""
        return self.name

    class Meta:
        """Мета-класс для модели Tag."""
        
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    """Модель ингредиента для рецептов."""

    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)

    def __str__(self):
        """Возвращает строковое представление ингредиента."""
        return f"{self.name} ({self.measurement_unit})"

    class Meta:
        """Мета-класс для модели Ingredient."""
        
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]


class Recipe(models.Model):
    """Основная модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        null=False
    )
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient'
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    short_link = models.SlugField(
        max_length=32,
        unique=True,
        blank=True,
        null=True
    )

    class Meta:
        """Мета-класс для модели Recipe."""
        
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def save(self, *args, **kwargs):
        """Сохраняет рецепт, генерируя короткую ссылку при необходимости."""
        if not self.short_link:
            self.short_link = generate_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        """Возвращает строковое представление рецепта."""
        return self.name


class RecipeIngredient(models.Model):
    """Модель для связи рецептов и ингредиентов с указанием количества."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveIntegerField()

    class Meta:
        """Мета-класс для модели RecipeIngredient."""
        
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление связи рецепта и ингредиента."""
        return f"{self.recipe}: {self.ingredient} - {self.amount}"


class Favorite(models.Model):
    """Модель для хранения избранных рецептов пользователей."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        """Мета-класс для модели Favorite."""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление избранного."""
        return f"{self.user} -> {self.recipe}"


class ShoppingCart(models.Model):
    """Модель корзины покупок пользователя."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    class Meta:
        """Мета-класс для модели ShoppingCart."""

        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление корзины."""
        return f"{self.user}: {self.recipe}"


class Subscription(models.Model):
    """Модель подписки пользователей друг на друга."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        """Мета-класс для модели Subscription."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f"{self.user} подписан на {self.author}"


def generate_hash() -> str:
    """Генерирует случайную строку для коротких ссылок.
    
    Returns:
        Случайная строка длиной от 15 до 32 символов.
    """
    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(15, 32)))


class LinkMapped(models.Model):
    """Модель для хранения сокращенных ссылок."""
    
    url_hash = models.CharField(max_length=32, unique=True)
    original_url = models.CharField(max_length=32)

    def save(self, *args, **kwargs):
        """Сохраняет ссылку, генерируя хеш при необходимости."""
        if not self.url_hash:
            self.url_hash = generate_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        """Возвращает строковое представление сокращенной ссылки."""
        return f"{self.url_hash} -> {self.original_url}"

    class Meta:
        """Мета-класс для модели LinkMapped."""

        verbose_name = 'Сокращенная ссылка'
        verbose_name_plural = 'Сокращенные ссылки'

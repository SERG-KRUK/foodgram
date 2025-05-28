"""Модели пользователи, ингредиенты, рецепты и связанные сущности."""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.core.exceptions import ValidationError

from .services import generate_hash
from api.constants import (
    TAG,
    INGREDIENT,
    MEASUREMENT_UNIT,
    RECIPE_NAME,
    EMAIL,
    USERNAME,
    FIRST_NAME,
    LAST_NAME,
    SHORT_URL_CODE,
)


class User(AbstractUser):
    """Модель пользователя с расширенными полями."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        max_length=EMAIL,
        unique=True,
        verbose_name='Email',
        help_text='Обязательное поле. Максимум 254 символа.',
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        }
    )
    username = models.CharField(
        max_length=USERNAME,
        unique=True,
        verbose_name='Username',
        help_text='Обязательное поле. Максимум 150 символов. Только буквы',
        error_messages={
            'unique': 'Пользователь с таким username уже существует.',
        },
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+\Z',
            message='Недопустимые символы в имени пользователя'
        )]
    )
    first_name = models.CharField(
        max_length=FIRST_NAME,
        verbose_name='Имя',
        help_text='Обязательное поле. Максимум 150 символов.'
    )
    last_name = models.CharField(
        max_length=LAST_NAME,
        verbose_name='Фамилия',
        help_text='Обязательное поле. Максимум 150 символов.'
    )
    avatar = models.ImageField(
        upload_to='users/',
        verbose_name='Аватар',
        blank=True
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Подписка',
    )

    class Meta:
        """Мета-класс для модели User."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        """Строковое представление пользователя."""
        return f'{self.get_full_name()} ({self.email})'


class Tag(models.Model):
    """Модель тега для рецептов."""

    name = models.CharField(
        max_length=TAG,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=TAG,
        unique=True,
        allow_unicode=True,
        verbose_name='Слаг'
    )

    class Meta:
        """Мета-класс для модели Tag."""

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        """Возвращает строковое представление тега."""
        return self.name[:20]


class Ingredient(models.Model):
    """Модель ингредиента для рецептов."""

    name = models.CharField(
        max_length=INGREDIENT,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT,
        verbose_name='Единица измерения'
    )

    class Meta:
        """Мета-класс для модели Ingredient."""

        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление ингредиента."""
        return f"{self.name[:20]} ({self.measurement_unit})"


class Recipe(models.Model):
    """Основная модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=RECIPE_NAME,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение'
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1)]
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    short_link = models.SlugField(
        max_length=SHORT_URL_CODE,
        unique=True,
        blank=True,
        verbose_name='Короткая ссылка'
    )

    class Meta:
        """Мета-класс для модели Recipe."""

        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def save(self, *args, **kwargs):
        """Сохраняет рецепт, генерируя короткую ссылку при необходимости."""
        if not self.short_link:
            self.short_link = generate_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        """Возвращает строковое представление рецепта."""
        return self.name[:20]


class RecipeIngredient(models.Model):
    """Модель для связи рецептов и ингредиентов с указанием количества."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        """Мета-класс для модели RecipeIngredient."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ['ingredient__name']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление связи рецепта и ингредиента."""
        return f"{self.recipe}: {self.ingredient} - {self.amount}"


class BaseUserRecipeRelation(models.Model):
    """Абстрактная модель для связи пользователя и рецепта."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        """Мета-класс для связи пользователя и рецепта."""

        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(app_label)s_%(class)s_unique'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление пользователя и рецепта."""
        return f"{self._meta.verbose_name}: {self.user} -> {self.recipe}"


class Favorite(BaseUserRecipeRelation):
    """Модель для хранения избранных рецептов пользователей."""

    class Meta(BaseUserRecipeRelation.Meta):
        """Мета-класс для модели Favorite."""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(BaseUserRecipeRelation):
    """Модель корзины покупок пользователя."""

    class Meta(BaseUserRecipeRelation.Meta):
        """Мета-класс для модели ShoppingCart."""

        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'


class Subscription(models.Model):
    """Модель подписки пользователей друг на друга."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        """Мета-класс для модели Subscription."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['author__last_name', 'author__first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def clean(self):
        """Функция с валидацией подписки."""
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя')

    def save(self, *args, **kwargs):
        """Функция с сохранением подписки."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f"{self.user} подписан на {self.author}"


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

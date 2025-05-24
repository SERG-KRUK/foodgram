"""Административная панель для управления моделями приложения recipes."""

from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import (
    Favorite,
    Ingredient,
    LinkMapped,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


class UserCreationForm(ModelForm):
    """Форма создания пользователя с обязательными ФИО."""

    class Meta:
        """Мета-класс для создания пользователя"""

        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        
    def clean(self):
        """функция валидации пользователя"""
        cleaned_data = super().clean()
        if not cleaned_data.get('first_name'):
            raise ValidationError("Имя обязательно для заполнения")
        if not cleaned_data.get('last_name'):
            raise ValidationError("Фамилия обязательна для заполнения")
        return cleaned_data


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административная панель для модели пользователя."""

    add_form = UserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username',
                       'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)


class RecipeIngredientInlineForm(ModelForm):
    """Форма для ингредиентов с валидацией количества."""

    def clean_amount(self):
        """функция для ингредиентов с валидацией количества."""
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Количество должно быть больше 0")
        return amount


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для отображения связи рецептов и ингредиентов."""

    model = RecipeIngredient
    form = RecipeIngredientInlineForm
    extra = 1
    min_num = 1


class RecipeAdminForm(ModelForm):
    """Форма рецепта с валидацией ингредиентов."""

    def clean(self):
        """функиця рецепта с валидацией ингредиентов."""
        cleaned_data = super().clean()
        if not self.instance.pk and not self.cleaned_data.get('ingredients'):
            raise ValidationError("Добавьте хотя бы один ингредиент")
        return cleaned_data


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административная панель для модели рецептов."""

    form = RecipeAdminForm
    list_display = ('name', 'author', 'cooking_time', 'favorites_count')
    list_filter = ('tags', 'author')
    search_fields = ('name', 'author__username',)
    inlines = [RecipeIngredientInline]
    exclude = ('ingredients',)

    @display(description='В избранном')
    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административная панель для модели ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административная панель для модели тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class SubscriptionAdminForm(ModelForm):
    """Форма подписки с проверкой на самоподписку."""

    def clean(self):
        """Форма подписки с проверкой на самоподписку."""
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        author = cleaned_data.get('author')

        if user and author and user == author:
            raise ValidationError("Нельзя подписаться на самого себя")
        return cleaned_data


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административная панель для модели подписок."""

    form = SubscriptionAdminForm
    list_display = ('user', 'author')
    list_filter = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Административная панель для модели избранного."""

    list_display = ('user', 'recipe')
    list_filter = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Административная панель для модели корзины покупок."""

    list_display = ('user', 'recipe')
    list_filter = ('user',)


admin.site.register(LinkMapped)

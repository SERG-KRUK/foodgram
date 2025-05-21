"""Административная панель для управления моделями приложения recipes."""

from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Favorite,
    Ingredient,
    LinkMapped,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


admin.site.register(LinkMapped)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административная панель для модели пользователя."""

    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для отображения связи рецептов и ингредиентов."""

    model = Recipe.ingredients.through
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административная панель для модели рецептов."""

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

    list_display = ('name', 'color_code', 'slug')
    search_fields = ('name', 'slug')

    @display(description='Цвет (HEX)')
    def color_code(self, obj):
        """Возвращает HEX-код цвета тега."""
        return obj.color


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


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административная панель для модели подписок."""

    list_display = ('user', 'author')
    list_filter = ('user',)

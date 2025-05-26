"""Административная панель для управления моделями приложения recipes."""

from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административная панель для модели пользователя."""

    list_display = ('email', 'username', 'first_name', 'last_name', 
                    'is_staff', 'recipes_count', 'subscribers_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    @display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @display(description='Подписчиков')
    def subscribers_count(self, obj):
        return obj.subscribers.count()


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для отображения связи рецептов и ингредиентов."""
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административная панель для модели рецептов."""

    list_display = ('name', 'author', 'cooking_time', 'image_preview',
                    'ingredients_list', 'tags_list', 'favorites_count')
    list_filter = ('tags', 'author')
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline]
    exclude = ('ingredients',)

    @display(description='Изображение')
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="80" height="60">')
        return "Нет изображения"

    @display(description='Ингредиенты')
    def ingredients_list(self, obj):
        return ", ".join(
            [ingredient.name for ingredient in obj.ingredients.all()])

    @display(description='Теги')
    def tags_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    @display(description='В избранном')
    def favorites_count(self, obj):
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


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административная панель для модели подписок."""

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


admin.site.unregister(Group)

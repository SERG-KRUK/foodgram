"""Filter for view class."""

from django.db.models import Q
from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    """Filter for view class."""
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.CharFilter(method='filter_tags')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')
    is_favorited = filters.BooleanFilter(method='filter_favorited')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']

    def filter_tags(self, queryset, name, value):
        return queryset.filter(tags__slug__in=value.split(',')).distinct()

    def filter_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        return queryset.filter(name__istartswith=value)

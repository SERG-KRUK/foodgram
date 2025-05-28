"""Вью рецептов для редиректа по короткой ссылке."""

from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def recipe_by_short_link(request, short_link):
    """Перенаправление по короткой ссылке на полный URL рецепта."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f'/recipes/{recipe.pk}/')

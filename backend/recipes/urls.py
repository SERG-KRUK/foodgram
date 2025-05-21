from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AdminIngredientViewSet, AdminTagViewSet, IngredientViewSet,
                    RecipeViewSet, TagViewSet, UserViewSet)

"""
This module defines the URL routing for the recipes application.
"""

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register(r'admin/tags', AdminTagViewSet, basename='admin-tags')
router.register(
    r'admin/ingredients', AdminIngredientViewSet, basename='admin-ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from .views import (UserViewSet, TagViewSet, IngredientViewSet, RecipeViewSet,
                    AdminTagViewSet, AdminIngredientViewSet,
                    get_ingredients, RecipeDetailView, recipe_by_short_link)
from django.conf import settings
from . import views
from django.conf.urls.static import static


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
    path('auth/', include('djoser.urls.authtoken')),]
    #path('s/<slug:short_link>/', recipe_by_short_link, name='recipe-short-link'),
    #path('api/ingredients/', get_ingredients),
    #path('api/recipes/<int:pk>/',
    #     RecipeDetailView.as_view(), name='recipe-api-detail'),
    #path('api/recipes/<int:pk>/get-link/', RecipeViewSet.as_view(
    #    {'get': 'get_link'}), name='recipe-get-link'),
#] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

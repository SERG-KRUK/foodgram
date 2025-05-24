from django.urls import include, path
from rest_framework.routers import DefaultRouter
from recipes.views import AdminTagViewSet, AdminIngredientViewSet

router = DefaultRouter()
router.register(r'admin/tags', AdminTagViewSet, basename='admin-tags')
router.register(
    r'admin/ingredients', AdminIngredientViewSet, basename='admin-ingredients')

urlpatterns = [
    path('', include(router.urls)),
]

"""View-классы для обработки запросов API приложения recipes."""

from rest_framework import viewsets

from .models import (
    Ingredient,
    Tag,
)
from api.permissions import IsAdmin
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
)


class AdminTagViewSet(viewsets.ModelViewSet):
    """ViewSet для администрирования тегов (только для администраторов)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdmin]
    pagination_class = None


class AdminIngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для администрирования ингредиентов (для администраторов)."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdmin]
    pagination_class = None

    def get_queryset(self):
        """Фильтрация ингредиентов по имени."""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset

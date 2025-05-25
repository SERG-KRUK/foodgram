"""This module defines the URL routing for the recipes application."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]

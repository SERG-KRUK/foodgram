"""Модуль для загрузки тегов по умолчанию."""

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    """Команда для загрузки стандартных тегов в базу данных."""

    help = 'Load default tags'

    def handle(self, *args, **options):
        """Загружает предустановленные теги в базу данных."""
        tags = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
            {'name': 'Десерт', 'slug': 'dessert'}
        ]

        for tag in tags:
            Tag.objects.get_or_create(**tag)

        self.stdout.write(self.style.SUCCESS('Теги успешно загружены'))

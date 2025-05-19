from django.core.management.base import BaseCommand
from recipes.models import Tag

class Command(BaseCommand):
    help = 'Load default tags'
    
    def handle(self, *args, **options):
        tags = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
            {'name': 'Десерт', 'slug': 'dessert'}
        ]
        
        for tag in tags:
            Tag.objects.get_or_create(**tag)
        
        self.stdout.write(self.style.SUCCESS('Теги успешно загружены'))
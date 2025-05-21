from django.core.management.base import BaseCommand
import csv
import json
import os

from recipes.models import Ingredient
from django.conf import settings


class Command(BaseCommand):
    help = 'Load ingredients from CSV or JSON file'

    def handle(self, *args, **options):
        # Пробуем загрузить из CSV
        csv_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')
        json_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')

        if os.path.exists(csv_path):
            self.load_from_csv(csv_path)
        elif os.path.exists(json_path):
            self.load_from_json(json_path)
        else:
            self.stdout.write(self.style.ERROR(
                'Файлы ingredients.csv и ingredients.json не найдены'))

    def load_from_csv(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if len(row) != 2:
                        continue

                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip()
                    )
                    count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно загружено {count} ингредиентов из CSV'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке CSV: {str(e)}'))

    def load_from_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            ingredients = json.load(f)
            count = 0
            for item in ingredients:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Успешно загружено {count} ингредиентов из JSON'))

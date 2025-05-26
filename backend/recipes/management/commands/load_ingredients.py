"""Модуль для загрузки ингридиентов по умолчанию."""

import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингридиентов по умолчанию."""

    help = 'Load ingredients from CSV or JSON file'

    def handle(self, *args, **options):
        """Загружает предустановленные рецепты в базу данных."""
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
        """Загружает предустановленные теги в базу данных."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                ingredients = []
                for row in reader:
                    if len(row) != 2:
                        continue

                    name, measurement_unit = row
                    ingredients.append(
                        Ingredient(
                            name=name.strip(),
                            measurement_unit=measurement_unit.strip()
                        )
                    )
                
                Ingredient.objects.bulk_create(
                    ingredients,
                    ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно загружено {len(ingredients)}'
                        f'ингредиентов из JSON'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке CSV: {str(e)}'))

    def load_from_json(self, file_path):
        """Загружает предустановленные теги в базу данных."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
                ingredients = [
                    Ingredient(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )
                    for item in ingredients_data
                ]
                
                Ingredient.objects.bulk_create(
                    ingredients,
                    ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно загружено {len(ingredients)}'
                        f'ингредиентов из JSON'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке JSON: {str(e)}'))

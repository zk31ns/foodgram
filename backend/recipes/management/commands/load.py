import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Команда для загрузки ингредиентов и тегов из CSV файла."""

    help = "Загрузка данных в БД из CSV файла"

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return

        # Загрузка ингредиентов
        with open(file_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            ingredients_to_create = []
            for row_num, row in enumerate(reader, start=1):
                if len(row) != 2:
                    self.stdout.write(
                        self.style.WARNING(f'Строка {row_num}: некорректное количество полей — {row}')
                    )
                    continue
                name, measurement_unit = [field.strip() for field in row]
                if not name or not measurement_unit:
                    self.stdout.write(
                        self.style.WARNING(f'Строка {row_num}: пустые поля — {row}')
                    )
                    continue
                ingredients_to_create.append(
                    Ingredient(name=name, measurement_unit=measurement_unit)
                )

            # Массовое создание без дубликатов
            created_count = 0
            for ingredient in ingredients_to_create:
                obj, created = Ingredient.objects.get_or_create(
                    name=ingredient.name,
                    measurement_unit=ingredient.measurement_unit
                )
                if created:
                    created_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'✅ Успешно загружено ингредиентов: {created_count}')
            )

        # Создание тегов
        tags_data = [
            {"name": "Завтрак", "slug": "breakfast", "color": "#E26C2D"},
            {"name": "Обед", "slug": "lunch", "color": "#49B64E"},
            {"name": "Ужин", "slug": "dinner", "color": "#8775D2"},
        ]

        created_tags = 0
        for tag_data in tags_data:
            obj, created = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults=tag_data
            )
            if created:
                created_tags += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ Успешно создано тегов: {created_tags}')
        )

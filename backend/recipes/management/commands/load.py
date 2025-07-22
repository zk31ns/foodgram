import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из CSV файла."""

    help = "Загрузка данных в БД из CSV файла"

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return

        with open(file_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) != 2:
                    continue  # Пропускаем некорректные строки
                name, measurement_unit = row
                name = name.strip()
                measurement_unit = measurement_unit.strip()
                if not name or not measurement_unit:
                    continue  # Пропускаем пустые
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
        self.stdout.write(
            self.style.SUCCESS('✅ Ингредиенты успешно загружены')
        )

        # Создание тегов
        Tag.objects.get_or_create(
            name="Завтрак", slug="breakfast", color="#E26C2D"
        )
        Tag.objects.get_or_create(
            name="Обед", slug="lunch", color="#49B64E"
        )
        Tag.objects.get_or_create(
            name="Ужин", slug="dinner", color="#8775D2"
        )
        self.stdout.write(self.style.SUCCESS('✅ Теги созданы'))

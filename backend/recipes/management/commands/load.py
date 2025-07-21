import csv
import os

from django.core.management.base import BaseCommand

from foodgram_backend.settings import BASE_DIR
from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из csv файла."""

    help = "loading data into db from scv file"

    def handle(self, *args, **options):
        with open(
            os.path.join(BASE_DIR, 'data', 'ingredients.csv'),
            encoding='UTF-8',
        ) as file_data:
            reader = csv.reader(file_data)
            for row in reader:
                name = row[0]
                measurement_unit = row[1]
                ingredient = Ingredient(
                    name=name,
                    measurement_unit=measurement_unit,
                )
                ingredient.save()
        self.stdout.write(
            self.style.SUCCESS('ingredient data uploaded successfully')
        )

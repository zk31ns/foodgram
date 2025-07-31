# import time
# from django.core.management.base import BaseCommand
# from django.db import connection
# from django.db.utils import OperationalError


# class Command(BaseCommand):
#     """Команда Django: ждёт, пока станет доступна БД."""

#     def handle(self, *args, **options):
#         self.stdout.write('Ожидание подключения к базе данных...')
#         db_conn = None
#         while not db_conn:
#             try:
#                 db_conn = connection.cursor()
#             except OperationalError:
#                 self.stdout.write('База недоступна, ждём 1 секунду...')
#                 time.sleep(1)
#         self.stdout.write(self.style.SUCCESS('✅ База данных доступна'))

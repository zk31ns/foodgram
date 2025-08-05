from rest_framework.pagination import PageNumberPagination
from api.constants import DEFAULT_PAGE_SIZE


class CustomPaginator(PageNumberPagination):
    """Пагинация с параметром limit и размером страницы по умолчанию 6."""
    page_size_query_param = 'limit'
    page_size = DEFAULT_PAGE_SIZE

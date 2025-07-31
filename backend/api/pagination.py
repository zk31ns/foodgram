from rest_framework.pagination import PageNumberPagination


class CustomPaginator(PageNumberPagination):
    """Пагинация с параметром limit и размером страницы по умолчанию 6."""
    page_size_query_param = 'limit'
    page_size = 6

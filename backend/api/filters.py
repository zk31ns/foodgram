import django_filters
from django.db.models import Q

from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    """Фильтр рецептов по тегам, автору, избранному и списку покупок."""
    tags = django_filters.CharFilter(method='filter_tags')
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    author = django_filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        ]

    def filter_queryset(self, queryset):
        """Явно применяем фильтры в нужном порядке."""
        queryset = super().filter_queryset(queryset)

        is_fav = self.data.get('is_favorited') == '1'
        if is_fav and self.request.user.is_authenticated:
            queryset = queryset.filter(
                favorite_related__user=self.request.user
            ).distinct()

        is_in_cart = self.data.get('is_in_shopping_cart') == '1'
        if is_in_cart and self.request.user.is_authenticated:
            queryset = queryset.filter(
                shoppingcart_related__user=self.request.user
            ).distinct()

        return queryset

    def filter_tags(self, queryset, name, value):
        """Фильтрует рецепты по списку тегов."""
        tag_slugs = self.request.query_params.getlist('tags')
        if tag_slugs:
            q_objects = Q()
            for slug in tag_slugs:
                q_objects |= Q(tags__slug=slug)
            return queryset.filter(q_objects).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты, добавленные в избранное."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_related__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты, добавленные в список покупок."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shoppingcart_related__user=self.request.user
            )
        return queryset


class IngredientSearchFilter(django_filters.FilterSet):
    """
    Фильтр ингредиентов по названию (поиск с начала слова).
    """
    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']

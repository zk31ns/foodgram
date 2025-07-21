import django_filters
from django_filters.rest_framework import FilterSet
from django.db.models import Q

from recipes.models import Recipe, Ingredient


class RecipeFilter(FilterSet):
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(method='filter_is_in_shopping_cart')
    author = django_filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset


class IngredientSearchFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_by_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_by_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).order_by('name')

import django_filters
from django.db.models import Q

from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_tags')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    author = django_filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        print("=== filter_tags called ===")
        print("Tags from request:", self.request.query_params.getlist('tags'))
        tag_slugs = self.request.query_params.getlist('tags')
        if tag_slugs:
            q_objects = Q()
            for slug in tag_slugs:
                print("Filtering by tag:", slug)
                q_objects |= Q(tags__slug=slug)
            result = queryset.filter(q_objects).distinct()
            print("Filtered count:", result.count())
            return result
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(recipe_favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset


class IngredientSearchFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']

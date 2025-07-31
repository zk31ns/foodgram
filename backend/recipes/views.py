from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe


def recipe_short_link_redirect(request, pk):
    """Редирект с /s/<id> на /recipes/<id>/"""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404("Рецепт не найден")
    return redirect(f'/recipes/{pk}/')

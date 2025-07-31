# backend/recipes/views.py
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def recipe_short_link_redirect(request, pk):
    """Редирект с /s/<id> на /recipes/<id>/"""
    # Проверяем, существует ли рецепт
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404("Рецепт не найден")
    return redirect(f'/recipes/{pk}/')

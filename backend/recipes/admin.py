from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInRecipeInline,)
    list_display = ('name', 'author', 'pub_date', 'favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    readonly_fields = ('favorites_count',)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.recipe_favorites.count()


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')

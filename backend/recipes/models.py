from django.db import models
from django.contrib.auth import get_user_model

from recipes.constants import (
    TAG_NAME_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        'Название', max_length=TAG_NAME_MAX_LENGTH, unique=True
    )
    slug = models.SlugField(
        'Слаг', max_length=TAG_NAME_MAX_LENGTH, unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=TAG_NAME_MAX_LENGTH)
    image = models.ImageField(
        'Изображение', upload_to='recipes/', blank=True, null=True
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField('Время приготовления (мин)')
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe'
    )

    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField('Количество')

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe'
            )
        ]


class UserRecipeRelation(models.Model):
    """Абстрактная базовая модель для связей пользователь-рецепт."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s_recipe'
            )
        ]


class Favorite(UserRecipeRelation):
    """Модель для избранных рецептов."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    """Модель для списка покупок."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

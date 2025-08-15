import base64
import re
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.constants import DEFAULT_RECIPES_LIMIT
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображений в формате base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для моделей, связывающих пользователя и рецепт.
    Предотвращает дублирование кода для Favorite, ShoppingCart и др.
    """
    class Meta:
        abstract = True
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=None,
                fields=('user', 'recipe')
            )
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.Meta.validators:
            self.Meta.validators[0].queryset = self.Meta.model.objects.all()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с подписками и аватаром."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

        extra_kwargs = {
            'is_subscribed': {'read_only': True},
        }

    def get_is_subscribed(self, obj):
        """Возвращает True, если текущий пользователь подписан на obj."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()

    def get_avatar(self, obj):
        """Возвращает полный URL аватара, если он существует."""
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки пользователя на автора."""
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        """Проверяет уникальность email и username, а также формат username."""
        if User.objects.filter(email=data['email']).exists():
            raise ValidationError({
                'email': 'Пользователь с таким email уже существует.'
            })
        if User.objects.filter(username=data['username']).exists():
            raise ValidationError({
                'username': 'Пользователь с таким username уже существует.'
            })
        if not re.match(r'^[\w.@+-]+$', data['username']):
            raise ValidationError({
                'username': 'Некорректный формат username.'
            })
        return data

    def create(self, validated_data):
        """Создаёт нового пользователя с хешированным паролем."""
        user = User.objects.create_user(**validated_data)
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки пользователя на автора."""
    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author')
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise ValidationError('Нельзя подписаться на себя')
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта для вложенных ответов."""
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        """Возвращает полный URL изображения рецепта."""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class SubscriptionUserSerializer(serializers.ModelSerializer):
    """Пользователь с рецептами и количеством подписок."""
    recipes = RecipeShortSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)  # ← Объявлено явно

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeWriteSerializer(serializers.Serializer):
    """Сериализатор для записи ингредиентов в рецепт."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов с тегами, ингредиентами и статусом."""
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        source='ingredientinrecipe_set'
    )
    author = UserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        """True, если рецепт в избранном у текущего пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorite_related.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """True, если рецепт в списке покупок у текущего пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shoppingcart_related.filter(user=request.user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов.
    Принимает данные, валидирует их и создаёт/обновляет рецепт.
    """
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientInRecipeWriteSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        """Проверяет данные: ингредиенты, теги, время приготовления."""
        ingredients_data = data.get('ingredients')
        if not ingredients_data:
            raise ValidationError({
                'ingredients': 'Нужно добавить хотя бы один ингредиент.'
            })

        ingredient_ids = [item['id'] for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })

        existing_ids = Ingredient.objects.filter(
            id__in=ingredient_ids
        ).values_list('id', flat=True)
        if len(existing_ids) != len(ingredient_ids):
            invalid_ids = set(ingredient_ids) - set(existing_ids)
            raise serializers.ValidationError({
                'ingredients': (
                    f'Ингредиенты с ID {list(invalid_ids)} '
                    'не существуют.'
                )
            })

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно добавить хотя бы один тег.'
            })

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны повторяться.'
            })

        cooking_time = data.get('cooking_time')
        if cooking_time is not None and cooking_time < 1:
            raise ValidationError({
                'cooking_time': (
                    f'Время приготовления должно быть '
                    f'не менее {cooking_time} минуты.'
                )
            })

        return data

    def create_ingredients(self, recipe, ingredients_data):
        """Создаёт связь рецепта с ингредиентами."""
        for item in ingredients_data:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=item['amount']
            )

    def create(self, validated_data):
        """Создаёт новый рецепт."""
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context['request'].user
        validated_data.pop('author', None)

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        instance = super().update(instance, validated_data)

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.ingredientinrecipe_set.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Возвращает сериализованные данные для чтения."""
        return RecipeReadSerializer(instance, context=self.context).data


class FavoriteSerializer(BaseUserRecipeSerializer):
    """
    Сериализатор для добавления/удаления рецепта из избранного.
    Используется в RecipeViewSet.favorite для валидации и создания.
    """
    class Meta(BaseUserRecipeSerializer.Meta):
        model = Favorite

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное'
            )

        return data


class ShoppingCartSerializer(BaseUserRecipeSerializer):
    """Сериализатор для добавления/удаления рецепта в список покупок."""
    class Meta(BaseUserRecipeSerializer.Meta):
        model = ShoppingCart


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки и удаления аватара пользователя."""
    avatar = Base64ImageField(
        required=True,
        error_messages={
            'required': 'Поле "avatar" обязательно для заполнения.'
        }
    )

    class Meta:
        model = User
        fields = ('avatar',)


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        """Проверяет, что текущий пароль верен."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError("Текущий пароль неверный")
        return value

    def validate_new_password(self, value):
        """Проверяет, что новый пароль отличается от текущего."""
        user = self.context['request'].user
        if user.check_password(value):
            raise ValidationError(
                "Новый пароль совпадает с текущим"
            )
        return value


# class SubscribeSerializer(serializers.ModelSerializer):
#     """Сериализатор для создания подписки."""
#     class Meta:
#         model = Subscription
#         fields = ('user', 'author')

#     def validate(self, data):
#         user = data['user']
#         author = data['author']

#         if user == author:
#             raise ValidationError('Нельзя подписаться на себя')

#         if Subscription.objects.filter(user=user, author=author).exists():
#             raise ValidationError('Вы уже подписаны на этого пользователя')

#         return data

#     def create(self, validated_data):
#         return Subscription.objects.create(**validated_data)

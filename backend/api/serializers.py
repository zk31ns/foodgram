# api/serializers.py
import base64
import re
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

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
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()  # Убедитесь, что он возвращает строку

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': 'Пользователь с таким email уже существует.'
            })
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({
                'username': 'Пользователь с таким username уже существует.'
            })
        if not re.match(r'^[\w.@+-]+$', data['username']):
            raise serializers.ValidationError({
                'username': 'Некорректный формат username.'
            })
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
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
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class SubscriptionUserSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        recipes = obj.recipes.all()[:3]
        return RecipeShortSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
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
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.recipe_favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.in_shopping_cart.filter(user=request.user).exists()


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
        # Проверка: хотя бы один ингредиент
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужно добавить хотя бы один ингредиент.'
            })

        # Проверка: ингредиенты не должны повторяться
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })

        # ✅ Проверка: хотя бы один тег
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно добавить хотя бы один тег.'
            })
        
        # Проверяем дубликаты тегов
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны повторяться.'
            })
    
        cooking_time = data.get('cooking_time')
        if cooking_time is not None and cooking_time < 1:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно быть не менее 1 минуты.'
            })

        return data

    def create_ingredients(self, recipe, ingredients_data):
        """Создаёт связь рецепта с ингредиентами."""
        for item in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=item['id'],
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

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем теги
        if tags_data is not None:
            instance.tags.set(tags_data)

        # Обновляем ингредиенты
        if ingredients_data is not None:
            instance.ingredientinrecipe_set.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Возвращает сериализованные данные для чтения (RecipeReadSerializer)."""
        return RecipeReadSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe')
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe')
            )
        ]


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверный")
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        if user.check_password(value):
            raise serializers.ValidationError("Новый пароль совпадает с текущим")
        return value

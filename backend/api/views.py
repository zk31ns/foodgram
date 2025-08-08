from django.db import models
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.pagination import CustomPaginator
from api.permissions import IsAuthorOrReadOnly, IsSelfOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    PasswordChangeSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionUserSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей."""
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    pagination_class = CustomPaginator
    permission_classes = [IsSelfOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['subscribe', 'subscriptions']:
            return SubscriptionUserSerializer
        return UserSerializer

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Профиль текущего пользователя."""
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='me-avatar'
    )
    def avatar(self, request):
        """Добавление или удаление аватара."""
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        pagination_class=CustomPaginator
    )
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан текущий пользователь.
        """
        user = request.user
        authors = User.objects.filter(
            following__user=user
        ).annotate(
            recipes_count=models.Count('recipes', distinct=True),
            is_subscribed=models.Exists(
                Subscription.objects.filter(
                    user=user,
                    author=models.OuterRef('pk')
                )
            )
        ).prefetch_related('recipes')

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionUserSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionUserSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """
        Подписаться или отписаться от пользователя.
        POST /api/users/{id}/subscribe/ → подписаться
        DELETE /api/users/{id}/subscribe/ → отписаться
        """
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            annotated_author = User.objects.annotate(
                recipes_count=models.Count('recipes', distinct=True),
                is_subscribed=models.Exists(
                    Subscription.objects.filter(
                        user=user,
                        author=models.OuterRef('pk')
                    )
                )
            ).get(pk=author.pk)

            serializer = SubscriptionUserSerializer(
                annotated_author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user,
                author=author
            ).delete()
            if not deleted:
                return Response(
                    {'errors': 'Вы не были подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """
        Изменение пароля пользователя.
        POST /api/users/set_password/
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientSearchFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer
    pagination_class = CustomPaginator
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @staticmethod
    def _add_to_list(
        serializer_class, request, pk, success_status=status.HTTP_201_CREATED
    ):
        """
        Приватный статический метод для добавления рецепта
        в список (избранное, корзина).
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            response_serializer = RecipeShortSerializer(
                recipe,
                context={'request': request}
            )
            return Response(response_serializer.data, status=success_status)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _remove_from_list(model, request, pk):
        """
        Удаляет связь пользователь-рецепт.
        Возвращает:
            - True, если объект был удалён
            - False, если не был найден
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        return deleted > 0

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить или удалить рецепт из избранного."""
        if request.method == 'POST':
            return self._add_to_list(FavoriteSerializer, request, pk)
        elif request.method == 'DELETE':
            removed = self._remove_from_list(Favorite, request, pk)
            if not removed:
                return Response(
                    {'errors': 'Рецепт не был в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить или удалить рецепт из корзины."""
        if request.method == 'POST':
            return self._add_to_list(ShoppingCartSerializer, request, pk)
        elif request.method == 'DELETE':
            removed = self._remove_from_list(ShoppingCart, request, pk)
            if not removed:
                return Response(
                    {'errors': 'Рецепт не был в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shoppingcart_related__user=request.user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount'))

        shopping_list = "Список покупок:\n\n"
        for item in ingredients:
            shopping_list += (
                f"{item['name']} ({item['measurement_unit']}) "
                f"— {item['amount']}\n"
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_path = f"/s/{recipe.id}"
        short_link = request.build_absolute_uri(short_path)
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

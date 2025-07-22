# api/views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, F

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.models import User, Subscription
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientInRecipe,
)

from api.serializers import (
    UserSerializer,
    UserCreateSerializer,
    SubscriptionSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    AvatarSerializer,
)
from api.pagination import CustomPaginator
from api.permissions import IsAuthorOrReadOnly, IsSelfOrReadOnly
from api.filters import RecipeFilter, IngredientSearchFilter


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPaginator
    permission_classes = [IsSelfOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
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
        permission_classes=[IsAuthenticated]
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

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Вьюсет для подписок."""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        author_id = request.data.get('author')
        author = get_object_or_404(User, id=author_id)
        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author
        )
        if not created:
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = SubscriptionUserSerializer(
            author,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не были подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite_add(self, request, pk=None):
        """Добавить рецепт в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в избранное'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def favorite_del(self, request, pk=None):
        """Удалить рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не был в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart_add(self, request, pk=None):
        """Добавить рецепт в корзину."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в список покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def shopping_cart_del(self, request, pk=None):
        """Удалить рецепт из корзины."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не был в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        ingredients = IngredientInRecipe.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount'))

        shopping_list = "Список покупок:\n\n"
        for item in ingredients:
            shopping_list += f"{item['name']} ({item['measurement_unit']}) — {item['amount']}\n"

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

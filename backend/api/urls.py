from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    UserViewSet,
    SubscriptionViewSet,
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'users/subscriptions', SubscriptionViewSet, basename='users-subscriptions')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

from django.contrib import admin
from django.urls import include, path

from recipes.views import recipe_short_link_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<int:pk>/',
        recipe_short_link_redirect,
        name='recipe-short-link'
    ),
]

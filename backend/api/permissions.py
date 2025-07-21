from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение: только автор может редактировать/удалять рецепт.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем безопасные методы (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверяем, является ли пользователь автором объекта
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение: только администратор может создавать/редактировать/удалять.
    """

    def has_permission(self, request, view):
        # Разрешаем безопасные методы всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверяем, является ли пользователь администратором
        return request.user.is_staff


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    Разрешение: пользователь может редактировать только свой профиль.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверяем, совпадает ли пользователь с объектом
        return obj == request.user

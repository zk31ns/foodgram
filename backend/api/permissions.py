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


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение: безопасные методы для всех, остальные — только для авторизованных.
    """

    def has_permission(self, request, view):
        # Все могут читать
        if request.method in permissions.SAFE_METHODS:
            return True
        # Только авторизованные могут создавать
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Для изменения/удаления — только автор
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    Разрешение: пользователь может редактировать только свой профиль.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверяем, совпадает ли пользователь с объектом
        return obj == request.user

from rest_framework import permissions


class AdminOrReadOnly(permissions.BasePermission):
    """Права доступа для админа."""

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated
                    and request.user.is_superuser))


class AuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Права доступа для авторов."""

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user.is_superuser)

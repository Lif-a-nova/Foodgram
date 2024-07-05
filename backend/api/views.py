from datetime import date

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscribe, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import AdminOrReadOnly, AuthorOrAdminOrReadOnly
from .serializers import (CustomUserSerializer,
                          IngredientSerializer, RecipeCartSerializer,
                          RecipeRetriveSerializer, RecipeSerializer,
                          SubscribeSerializer, SubscriptionsSerializer,
                          TagSerializer)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    search_fields = ('username', 'email',)
    permission_classes = [AuthorOrAdminOrReadOnly]
    serializer_class = CustomUserSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Функция подписки/отписки на автора."""
        subscriber = request.user
        sub_author = get_object_or_404(User, id=id)
        instance = Subscribe.objects.filter(user=subscriber, author=sub_author)
        if request.method == 'POST':
            if instance.exists():
                return Response(
                    {"errors": 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST)
            if subscriber == sub_author:
                return Response(
                    {"errors": 'Нельзя подписаться на себя.'},
                    status=status.HTTP_400_BAD_REQUEST)

            serializer = SubscribeSerializer(
                sub_author, data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=subscriber, author=sub_author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not instance.exists():
            return Response(
                {"errors": 'Вы не подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        """Функция возвращает список подписок."""
        sub_authors = User.objects.filter(sub_author__user=request.user)
        paginated_queryset = self.paginate_queryset(sub_authors)
        serializer = SubscriptionsSerializer(
            paginated_queryset, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AdminOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [AuthorOrAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    ordering = ('pub_date',)

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeRetriveSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=['POST', 'DELETE'],
    )
    def favorite(self, request, pk=None):
        """Функция добавляет/удаляет рецепт из избраннго."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        instance = FavoriteRecipe.objects.filter(user=user, recipe=recipe)
        if request.method == 'POST':
            if instance.exists():
                return Response({'errors': 'Рецепт уже добавлен '
                                 'в избранное.'},
                                status=status.HTTP_400_BAD_REQUEST)
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = RecipeCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not instance.exists():
            return Response(
                {'errors': ('Рецепт не был добавлен в избранное '
                            'или уже удален.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['POST', 'DELETE'],
    )
    def shopping_cart(self, request, pk=None):
        """Функция добавляет/удаляет рецепт из списока покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        instance = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if request.method == 'POST':
            if instance.exists():
                return Response({'errors': ('Рецепт уже добавлен в '
                                            'список покупок.')},
                                status=status.HTTP_400_BAD_REQUEST
                                )

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not instance.exists():
                return Response(
                    {'errors': ('Рецепт не был добавлен в список покупок '
                                'или уже удален.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': ('Запрос не понятен')},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False, methods=['GET'],
    )
    def download_shopping_cart(self, request):
        """Функция скачивает список покупок."""
        user = request.user
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(
            ingredient_amount=Sum('amount')
        )

        today = date.today()
        shopping_list = [f'{today}\n''Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} ({unit}) - {amount}')

        filename = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Tag
from users.models import User


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(filters.FilterSet):
    author = filters.ModelChoiceFilter(
        queryset=User.objects.all()
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = filters.CharFilter(
        method='get_is_favorited',
    )
    is_in_shopping_cart = filters.CharFilter(
        method='get_is_in_shopping_cart',
    )

    def get_is_favorited(self, queryset, filter_name, filter_value):
        if filter_value:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, filter_name, filter_value):
        if filter_value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

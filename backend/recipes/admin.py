from django.contrib import admin

from .models import (FavoriteRecipe, Ingredient, IngredientRecipe,
                     Recipe, ShoppingCart, Tag)

EMPTY_VALUE = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = EMPTY_VALUE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug',)
    search_fields = ('name',)
    empty_value_display = EMPTY_VALUE


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = ('user',)
    list_filter = ('recipe',)
    empty_value_display = EMPTY_VALUE


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = ('user',)
    list_filter = ('recipe',)
    empty_value_display = EMPTY_VALUE


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'pub_date',
                    'is_favorited', 'cooking_time')
    search_fields = ('name',)
    list_filter = ('name', 'author', 'tags',)
    readonly_fields = ('is_favorited',)
    inlines = (IngredientRecipeInline,)
    empty_value_display = EMPTY_VALUE

    def is_favorited(self, obj):
        return FavoriteRecipe.objects.filter(recipe=obj).count()

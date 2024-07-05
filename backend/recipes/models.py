from django.contrib.auth import get_user_model
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator)
from django.db import models

User = get_user_model()


CROP_TEXT: int = 15


class Ingredient(models.Model):
    """ Модель Ингредиент."""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Tag(models.Model):
    """ Модель Тег Рецепта."""
    name = models.CharField(
        unique=True,
        verbose_name='Название тега',
        max_length=200
    )
    color = models.CharField(
        unique=True,
        verbose_name='Цвет HEX-код',
        max_length=7,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Введите цвет в формате HEX.'
            )
        ]
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг тега',
        max_length=200
    )

    # весь прикол в маленьких буквах, я поняла))))
    def clean(self):
        self.color = self.color.upper()

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(
                fields=['color', 'slug'],
                name='unique_color',
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """ Модель Рецепт."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='IngredientRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(1, 'Минимальное время - 1 мин.'),
            MaxValueValidator(500, 'Максимальное времени - 500 мин.')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:CROP_TEXT]


class IngredientRecipe(models.Model):
    """ Модель связи Ингредиент-Рецепт количество."""
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='ingredient_recipe',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='recipe_ingredient',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, 'Минимальное количество - 1.'),
            MaxValueValidator(3000, 'Максимальное количество - 3000.')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепта'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'Рецепт "{self.recipe}" включает {self.ingredient}.'


class FavoriteRecipe(models.Model):
    """ Модель Избранные Рецепты."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favoriter',
        verbose_name='Гурман'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        ordering = ['-user']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe',
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в Избранное {self.recipe}.'


class ShoppingCart(models.Model):
    """ Модель Список Покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopper',
        verbose_name='Покупатель'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт в списке покупок'
    )

    class Meta:
        ordering = ['-recipe']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart_recipe',
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в Список покупок {self.recipe}.'

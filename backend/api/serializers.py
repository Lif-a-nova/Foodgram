from djoser.serializers import UserSerializer
from rest_framework import serializers

from recipes.models import (FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscribe, User

from .fields import Base64ImageField


class CustomUserSerializer(UserSerializer):
    """Сериализатор - просмотр пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор - создание/удаление подписок."""
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Subscribe
        fields = ('user', 'author')

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return SubscriptionsSerializer(instance, context=context).data


class SubscriptionsSerializer(CustomUserSerializer):
    """Сериализатор - просмотр подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeCartSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class RecipeCartSerializer(serializers.ModelSerializer):
    """Сериализатор - мин. информация рецепта."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор - информация тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор - информация ингриндиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор - добавление ингриндиента."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(self, data):
        if data < 1:
            raise serializers.ValidationError(
                'Укажите количество больше 0.'
            )
        if data > 10000:
            raise serializers.ValidationError(
                'Укажите количество меньше 10000.'
            )
        return data


class IngredientFullSerializer(IngredientSerializer):
    """Сериализатор - вся инфа ингриндиента."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """"Сериализатор - создание/изменение рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def validate_tags(self, data):
        if not data:
            raise serializers.ValidationError(
                'Выберите хотя бы один тэг.'
            )
        for tag_name in data:
            if not Tag.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    'Такого тэга нет.'
                )
        if len(data) != len(set(data)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        return data

    def validate_ingredients(self, data):
        if len(data) < 1:
            raise serializers.ValidationError(
                'Выберите хотя бы один ингредиент.'
            )
        ingredients = []
        for i, val in enumerate(data):
            if not Ingredient.objects.filter(id=val['id']).exists():
                raise serializers.ValidationError(
                    'Выберите ингредиент из доступных.'
                )
            ingredients.append(val['id'])
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return data

    def validate_cooking_time(self, data):
        if int(data) < 1:
            raise serializers.ValidationError(
                'Минимальное время приготовления 1 мин.'
            )
        if int(data) > 500:
            raise serializers.ValidationError(
                'Максимальное времени приготовления 500 мин.'
            )
        return data

    def create_tags(self, tags, recipe):
        for tag in tags:
            recipe.tags.add(tag)

    def create_ingredients(self, ingredients, recipe):
        for i in ingredients:
            ingredient = Ingredient.objects.get(id=i['id'])
            IngredientRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=i['amount'])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients=ingredients, recipe=recipe)
        self.create_tags(tags=tags, recipe=recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if isinstance(validated_data['tags'], list):
            tags = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.set(tags)
        if isinstance(validated_data['ingredients'], list):
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeRetriveSerializer(instance, context=context).data


class RecipeRetriveSerializer(serializers.ModelSerializer):
    """"Сериализатор - просмотр рецепта."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientFullSerializer(
        many=True, read_only=True,
        source='recipe_ingredient'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user.id
        recipe = obj.id
        return FavoriteRecipe.objects.filter(
            user_id=user,
            recipe_id=recipe
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user.id
        recipe = obj.id
        return ShoppingCart.objects.filter(
            user_id=user,
            recipe_id=recipe
        ).exists()

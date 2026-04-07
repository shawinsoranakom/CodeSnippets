def setUpTestData(cls):
        cls.pea = Ingredient.objects.create(iname="pea")
        cls.potato = Ingredient.objects.create(iname="potato")
        cls.tomato = Ingredient.objects.create(iname="tomato")
        cls.curry = Recipe.objects.create(rname="curry")
        RecipeIngredient.objects.create(recipe=cls.curry, ingredient=cls.potato)
        RecipeIngredient.objects.create(recipe=cls.curry, ingredient=cls.pea)
        RecipeIngredient.objects.create(recipe=cls.curry, ingredient=cls.tomato)
def test_aggregate_and_annotate_duplicate_columns_proxy(self):
        author = AuthorProxy.objects.latest("pk")
        recipe = RecipeProxy.objects.create(name="Dahl", author=author)
        recipe.tasters.add(author)
        recipes = RecipeProxy.objects.values("pk").annotate(
            name=F("author__name"),
            num_tasters=Count("tasters"),
        )
        self.assertSequenceEqual(
            recipes,
            [{"pk": recipe.pk, "name": "Stuart Russell", "num_tasters": 1}],
        )
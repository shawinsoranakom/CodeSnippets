def test_aggregate_and_annotate_duplicate_columns_unmanaged(self):
        author = AuthorProxy.objects.latest("pk")
        recipe = RecipeProxy.objects.create(name="Dahl", author=author)
        recipe.tasters.add(author)
        recipes = RecipeUnmanaged.objects.values("pk").annotate(
            name=F("author__age"),
            num_tasters=Count("tasters"),
        )
        self.assertSequenceEqual(
            recipes,
            [{"pk": recipe.pk, "name": 46, "num_tasters": 1}],
        )
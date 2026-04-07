def test_aggregate_group_by_unseen_columns_unmanaged(self):
        author = AuthorProxy.objects.latest("pk")
        shadow_author = AuthorProxy.objects.create(name=author.name, age=author.age - 2)
        recipe = RecipeProxy.objects.create(name="Dahl", author=author)
        shadow_recipe = RecipeProxy.objects.create(
            name="Shadow Dahl",
            author=shadow_author,
        )
        recipe.tasters.add(shadow_author)
        shadow_recipe.tasters.add(author)
        # This selects how many tasters each author had according to a
        # calculated field "name". The table has a column "name" that Django is
        # unaware of, and is equal for the two authors. The grouping column
        # cannot be referenced by its name ("name"), as it'd return one result
        # which is incorrect.
        author_recipes = (
            AuthorUnmanaged.objects.annotate(
                name=Concat(
                    Value("Writer at "),
                    Cast(F("age"), output_field=CharField()),
                )
            )
            .values("name")  # Field used for grouping.
            .annotate(num_recipes=Count("recipeunmanaged"))
            .filter(num_recipes__gt=0)
            .values("num_recipes")  # Drop grouping column.
        )
        self.assertSequenceEqual(
            author_recipes,
            [{"num_recipes": 1}, {"num_recipes": 1}],
        )
def test_unique_constraint_nulls_distinct(self):
        class Model(models.Model):
            name = models.CharField(max_length=10)

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["name"],
                        name="name_uq_distinct_null",
                        nulls_distinct=True,
                    ),
                ]

        warn = Warning(
            f"{connection.display_name} does not support "
            "UniqueConstraint.nulls_distinct.",
            hint=(
                "A constraint won't be created. Silence this warning if you don't care "
                "about it."
            ),
            obj=Model,
            id="models.W047",
        )
        expected = (
            []
            if connection.features.supports_nulls_distinct_unique_constraints
            else [warn]
        )
        self.assertEqual(Model.check(databases=self.databases), expected)
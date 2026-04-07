def test_unique_constraint_with_include(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["age"],
                        name="unique_age_include_id",
                        include=["id"],
                    ),
                ]

        errors = Model.check(databases=self.databases)
        expected = (
            []
            if connection.features.supports_covering_indexes
            else [
                Warning(
                    "%s does not support unique constraints with non-key columns."
                    % connection.display_name,
                    hint=(
                        "A constraint won't be created. Silence this warning if "
                        "you don't care about it."
                    ),
                    obj=Model,
                    id="models.W039",
                ),
            ]
        )
        self.assertEqual(errors, expected)
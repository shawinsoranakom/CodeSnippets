def test_index_with_condition(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                indexes = [
                    models.Index(
                        fields=["age"],
                        name="index_age_gte_10",
                        condition=models.Q(age__gte=10),
                    ),
                ]

        errors = Model.check(databases=self.databases)
        expected = (
            []
            if connection.features.supports_partial_indexes
            else [
                Warning(
                    "%s does not support indexes with conditions."
                    % connection.display_name,
                    hint=(
                        "Conditions will be ignored. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=Model,
                    id="models.W037",
                )
            ]
        )
        self.assertEqual(errors, expected)
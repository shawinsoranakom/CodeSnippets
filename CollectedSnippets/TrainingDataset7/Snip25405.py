def test_unique_constraint_with_condition(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["age"],
                        name="unique_age_gte_100",
                        condition=models.Q(age__gte=100),
                    ),
                ]

        errors = Model.check(databases=self.databases)
        expected = (
            []
            if connection.features.supports_partial_indexes
            else [
                Warning(
                    "%s does not support unique constraints with conditions."
                    % connection.display_name,
                    hint=(
                        "A constraint won't be created. Silence this warning if "
                        "you don't care about it."
                    ),
                    obj=Model,
                    id="models.W036",
                ),
            ]
        )
        self.assertEqual(errors, expected)
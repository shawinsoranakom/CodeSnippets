def test_deferrable_unique_constraint(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["age"],
                        name="unique_age_deferrable",
                        deferrable=models.Deferrable.DEFERRED,
                    ),
                ]

        errors = Model.check(databases=self.databases)
        expected = (
            []
            if connection.features.supports_deferrable_unique_constraints
            else [
                Warning(
                    "%s does not support deferrable unique constraints."
                    % connection.display_name,
                    hint=(
                        "A constraint won't be created. Silence this warning if "
                        "you don't care about it."
                    ),
                    obj=Model,
                    id="models.W038",
                ),
            ]
        )
        self.assertEqual(errors, expected)
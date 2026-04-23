def test_func_unique_constraint(self):
        class Model(models.Model):
            name = models.CharField(max_length=10)

            class Meta:
                constraints = [
                    models.UniqueConstraint(Lower("name"), name="lower_name_uq"),
                ]

        warn = Warning(
            "%s does not support unique constraints on expressions."
            % connection.display_name,
            hint=(
                "A constraint won't be created. Silence this warning if you "
                "don't care about it."
            ),
            obj=Model,
            id="models.W044",
        )
        expected = [] if connection.features.supports_expression_indexes else [warn]
        self.assertEqual(Model.check(databases=self.databases), expected)
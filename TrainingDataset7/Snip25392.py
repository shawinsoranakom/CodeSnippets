def test_check_constraints(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        condition=models.Q(age__gte=18), name="is_adult"
                    )
                ]

        errors = Model.check(databases=self.databases)
        warn = Warning(
            "%s does not support check constraints." % connection.display_name,
            hint=(
                "A constraint won't be created. Silence this warning if you "
                "don't care about it."
            ),
            obj=Model,
            id="models.W027",
        )
        expected = (
            [] if connection.features.supports_table_check_constraints else [warn]
        )
        self.assertCountEqual(errors, expected)
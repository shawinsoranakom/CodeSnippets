def test_func_unique_constraint_pointing_to_missing_field(self):
        class Model(models.Model):
            class Meta:
                constraints = [
                    models.UniqueConstraint(Lower("missing_field").desc(), name="name"),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'constraints' refers to the nonexistent field 'missing_field'.",
                    obj=Model,
                    id="models.E012",
                ),
            ],
        )
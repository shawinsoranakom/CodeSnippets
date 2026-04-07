def test_func_unique_constraint_pointing_to_missing_field_nested(self):
        class Model(models.Model):
            class Meta:
                constraints = [
                    models.UniqueConstraint(Abs(Round("missing_field")), name="name"),
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
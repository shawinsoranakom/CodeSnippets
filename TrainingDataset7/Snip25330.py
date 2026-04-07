def test_func_index_pointing_to_missing_field_nested(self):
        class Model(models.Model):
            class Meta:
                indexes = [
                    models.Index(Abs(Round("missing_field")), name="name"),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'indexes' refers to the nonexistent field 'missing_field'.",
                    obj=Model,
                    id="models.E012",
                ),
            ],
        )
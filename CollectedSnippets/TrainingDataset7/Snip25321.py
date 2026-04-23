def test_index_include_pointing_to_missing_field(self):
        class Model(models.Model):
            class Meta:
                indexes = [
                    models.Index(fields=["id"], include=["missing_field"], name="name"),
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
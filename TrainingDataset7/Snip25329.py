def test_func_index_pointing_to_missing_field(self):
        class Model(models.Model):
            class Meta:
                indexes = [models.Index(Lower("missing_field").desc(), name="name")]

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
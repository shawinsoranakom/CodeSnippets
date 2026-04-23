def test_func_index_complex_expression_custom_lookup(self):
        class Model(models.Model):
            height = models.IntegerField()
            weight = models.IntegerField()

            class Meta:
                indexes = [
                    models.Index(
                        models.F("height")
                        / (models.F("weight__abs") + models.Value(5)),
                        name="name",
                    ),
                ]

        with register_lookup(models.IntegerField, Abs):
            self.assertEqual(Model.check(databases=self.databases), [])
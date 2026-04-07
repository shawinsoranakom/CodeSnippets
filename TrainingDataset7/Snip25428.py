def test_func_unique_constraint_expression_custom_lookup(self):
        class Model(models.Model):
            height = models.IntegerField()
            weight = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        models.F("height")
                        / (models.F("weight__abs") + models.Value(5)),
                        name="name",
                    ),
                ]

        with register_lookup(models.IntegerField, Abs):
            self.assertEqual(Model.check(databases=self.databases), [])
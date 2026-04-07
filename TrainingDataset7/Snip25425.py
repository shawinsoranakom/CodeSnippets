def test_func_unique_constraint_required_db_features(self):
        class Model(models.Model):
            name = models.CharField(max_length=10)

            class Meta:
                constraints = [
                    models.UniqueConstraint(Lower("name"), name="lower_name_unq"),
                ]
                required_db_features = {"supports_expression_indexes"}

        self.assertEqual(Model.check(databases=self.databases), [])
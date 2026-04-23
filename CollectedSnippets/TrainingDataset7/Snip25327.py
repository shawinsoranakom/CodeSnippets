def test_func_index_required_db_features(self):
        class Model(models.Model):
            name = models.CharField(max_length=10)

            class Meta:
                indexes = [models.Index(Lower("name"), name="index_lower_name")]
                required_db_features = {"supports_expression_indexes"}

        self.assertEqual(Model.check(databases=self.databases), [])
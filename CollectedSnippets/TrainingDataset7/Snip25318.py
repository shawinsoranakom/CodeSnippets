def test_index_with_condition_required_db_features(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                required_db_features = {"supports_partial_indexes"}
                indexes = [
                    models.Index(
                        fields=["age"],
                        name="index_age_gte_10",
                        condition=models.Q(age__gte=10),
                    ),
                ]

        self.assertEqual(Model.check(databases=self.databases), [])
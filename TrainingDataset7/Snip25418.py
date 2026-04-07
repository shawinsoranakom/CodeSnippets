def test_unique_constraint_with_include_required_db_features(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                required_db_features = {"supports_covering_indexes"}
                constraints = [
                    models.UniqueConstraint(
                        fields=["age"],
                        name="unique_age_include_id",
                        include=["id"],
                    ),
                ]

        self.assertEqual(Model.check(databases=self.databases), [])
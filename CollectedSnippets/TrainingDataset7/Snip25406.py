def test_unique_constraint_with_condition_required_db_features(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                required_db_features = {"supports_partial_indexes"}
                constraints = [
                    models.UniqueConstraint(
                        fields=["age"],
                        name="unique_age_gte_100",
                        condition=models.Q(age__gte=100),
                    ),
                ]

        self.assertEqual(Model.check(databases=self.databases), [])
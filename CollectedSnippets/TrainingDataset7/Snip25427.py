def test_unique_constraint_nulls_distinct_required_db_features(self):
        class Model(models.Model):
            name = models.CharField(max_length=10)

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["name"],
                        name="name_uq_distinct_null",
                        nulls_distinct=True,
                    ),
                ]
                required_db_features = {"supports_nulls_distinct_unique_constraints"}

        self.assertEqual(Model.check(databases=self.databases), [])
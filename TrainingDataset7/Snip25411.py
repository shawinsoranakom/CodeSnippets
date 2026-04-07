def test_deferrable_unique_constraint_required_db_features(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                required_db_features = {"supports_deferrable_unique_constraints"}
                constraints = [
                    models.UniqueConstraint(
                        fields=["age"],
                        name="unique_age_deferrable",
                        deferrable=models.Deferrable.IMMEDIATE,
                    ),
                ]

        self.assertEqual(Model.check(databases=self.databases), [])
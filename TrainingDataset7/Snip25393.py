def test_check_constraints_required_db_features(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                required_db_features = {"supports_table_check_constraints"}
                constraints = [
                    models.CheckConstraint(
                        condition=models.Q(age__gte=18), name="is_adult"
                    )
                ]

        self.assertEqual(Model.check(databases=self.databases), [])
def test_check_constraint_pointing_to_missing_field(self):
        class Model(models.Model):
            class Meta:
                required_db_features = {"supports_table_check_constraints"}
                constraints = [
                    models.CheckConstraint(
                        name="name",
                        condition=models.Q(missing_field=2),
                    ),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            (
                [
                    Error(
                        "'constraints' refers to the nonexistent field "
                        "'missing_field'.",
                        obj=Model,
                        id="models.E012",
                    ),
                ]
                if connection.features.supports_table_check_constraints
                else []
            ),
        )
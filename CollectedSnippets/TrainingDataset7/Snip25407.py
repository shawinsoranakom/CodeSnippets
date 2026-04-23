def test_unique_constraint_condition_pointing_to_missing_field(self):
        class Model(models.Model):
            age = models.SmallIntegerField()

            class Meta:
                required_db_features = {"supports_partial_indexes"}
                constraints = [
                    models.UniqueConstraint(
                        name="name",
                        fields=["age"],
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
                if connection.features.supports_partial_indexes
                else []
            ),
        )
def test_unique_constraint_condition_pointing_to_joined_fields(self):
        class Model(models.Model):
            age = models.SmallIntegerField()
            parent = models.ForeignKey("self", models.CASCADE)

            class Meta:
                required_db_features = {"supports_partial_indexes"}
                constraints = [
                    models.UniqueConstraint(
                        name="name",
                        fields=["age"],
                        condition=models.Q(parent__age__lt=2),
                    ),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            (
                [
                    Error(
                        "'constraints' refers to the joined field 'parent__age__lt'.",
                        obj=Model,
                        id="models.E041",
                    )
                ]
                if connection.features.supports_partial_indexes
                else []
            ),
        )
def test_unique_constraint_pointing_to_reverse_o2o(self):
        class Model(models.Model):
            parent = models.OneToOneField("self", models.CASCADE)

            class Meta:
                required_db_features = {"supports_partial_indexes"}
                constraints = [
                    models.UniqueConstraint(
                        fields=["parent"],
                        name="name",
                        condition=models.Q(model__isnull=True),
                    ),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            (
                [
                    Error(
                        "'constraints' refers to the nonexistent field 'model'.",
                        obj=Model,
                        id="models.E012",
                    ),
                ]
                if connection.features.supports_partial_indexes
                else []
            ),
        )
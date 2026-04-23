def test_check_constraint_pointing_to_reverse_o2o(self):
        class Model(models.Model):
            parent = models.OneToOneField("self", models.CASCADE)

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        name="name",
                        condition=models.Q(model__isnull=True),
                    ),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'constraints' refers to the nonexistent field 'model'.",
                    obj=Model,
                    id="models.E012",
                ),
            ],
        )
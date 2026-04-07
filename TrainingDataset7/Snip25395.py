def test_check_constraint_pointing_to_reverse_fk(self):
        class Model(models.Model):
            parent = models.ForeignKey("self", models.CASCADE, related_name="parents")

            class Meta:
                constraints = [
                    models.CheckConstraint(name="name", condition=models.Q(parents=3)),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'constraints' refers to the nonexistent field 'parents'.",
                    obj=Model,
                    id="models.E012",
                ),
            ],
        )
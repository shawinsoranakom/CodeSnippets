def test_unique_constraint_include_pointing_to_m2m_field(self):
        class Model(models.Model):
            m2m = models.ManyToManyField("self")

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["id"],
                        include=["m2m"],
                        name="name",
                    ),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'constraints' refers to a ManyToManyField 'm2m', but "
                    "ManyToManyFields are not permitted in 'constraints'.",
                    obj=Model,
                    id="models.E013",
                ),
            ],
        )
def test_check_constraint_pointing_to_m2m_field(self):
        class Model(models.Model):
            m2m = models.ManyToManyField("self")

            class Meta:
                constraints = [
                    models.CheckConstraint(name="name", condition=models.Q(m2m=2)),
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
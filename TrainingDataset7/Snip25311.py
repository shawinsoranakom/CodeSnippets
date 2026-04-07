def test_pointing_to_m2m_field(self):
        class Model(models.Model):
            m2m = models.ManyToManyField("self")

            class Meta:
                indexes = [models.Index(fields=["m2m"], name="name")]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'indexes' refers to a ManyToManyField 'm2m', but "
                    "ManyToManyFields are not permitted in 'indexes'.",
                    obj=Model,
                    id="models.E013",
                ),
            ],
        )
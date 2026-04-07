def test_pointing_to_m2m(self):
        class Model(models.Model):
            m2m = models.ManyToManyField("self")

            class Meta:
                unique_together = [["m2m"]]

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'unique_together' refers to a ManyToManyField 'm2m', but "
                    "ManyToManyFields are not permitted in 'unique_together'.",
                    obj=Model,
                    id="models.E013",
                ),
            ],
        )
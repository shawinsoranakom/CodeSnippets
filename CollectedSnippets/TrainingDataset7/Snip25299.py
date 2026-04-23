def test_non_iterable(self):
        class Model(models.Model):
            class Meta:
                unique_together = 42

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'unique_together' must be a list or tuple.",
                    obj=Model,
                    id="models.E010",
                ),
            ],
        )
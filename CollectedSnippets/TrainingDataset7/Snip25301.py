def test_non_list(self):
        class Model(models.Model):
            class Meta:
                unique_together = "not-a-list"

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
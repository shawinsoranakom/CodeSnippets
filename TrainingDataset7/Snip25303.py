def test_pointing_to_missing_field(self):
        class Model(models.Model):
            class Meta:
                unique_together = [["missing_field"]]

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'unique_together' refers to the nonexistent field "
                    "'missing_field'.",
                    obj=Model,
                    id="models.E012",
                ),
            ],
        )
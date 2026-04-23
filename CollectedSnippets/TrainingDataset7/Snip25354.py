def test_ordering_pointing_to_missing_field(self):
        class Model(models.Model):
            class Meta:
                ordering = ("missing_field",)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'ordering' refers to the nonexistent field, related field, "
                    "or lookup 'missing_field'.",
                    obj=Model,
                    id="models.E015",
                )
            ],
        )
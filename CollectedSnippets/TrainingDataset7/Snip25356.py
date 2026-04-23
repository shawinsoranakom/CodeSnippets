def test_ordering_pointing_to_missing_related_field(self):
        class Model(models.Model):
            test = models.IntegerField()

            class Meta:
                ordering = ("missing_related__id",)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'ordering' refers to the nonexistent field, related field, "
                    "or lookup 'missing_related__id'.",
                    obj=Model,
                    id="models.E015",
                )
            ],
        )
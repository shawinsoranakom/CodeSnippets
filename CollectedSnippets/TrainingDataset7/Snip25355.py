def test_ordering_pointing_to_missing_foreignkey_field(self):
        class Model(models.Model):
            missing_fk_field = models.IntegerField()

            class Meta:
                ordering = ("missing_fk_field_id",)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'ordering' refers to the nonexistent field, related field, "
                    "or lookup 'missing_fk_field_id'.",
                    obj=Model,
                    id="models.E015",
                )
            ],
        )
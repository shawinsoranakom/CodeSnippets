def test_non_nullable_blank(self):
        class Model(models.Model):
            field = models.GenericIPAddressField(null=False, blank=True)

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    (
                        "GenericIPAddressFields cannot have blank=True if null=False, "
                        "as blank values are stored as nulls."
                    ),
                    obj=field,
                    id="fields.E150",
                ),
            ],
        )
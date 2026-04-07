def test_nullable_primary_key(self):
        class Model(models.Model):
            field = models.IntegerField(primary_key=True, null=True)

        field = Model._meta.get_field("field")
        with mock.patch.object(
            connection.features, "interprets_empty_strings_as_nulls", False
        ):
            results = field.check()
        self.assertEqual(
            results,
            [
                Error(
                    "Primary keys must not have null=True.",
                    hint=(
                        "Set null=False on the field, or remove primary_key=True "
                        "argument."
                    ),
                    obj=field,
                    id="fields.E007",
                ),
            ],
        )
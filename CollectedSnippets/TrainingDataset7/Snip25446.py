def test_str_default_value(self):
        class Model(models.Model):
            field = models.BinaryField(default="test")

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "BinaryField's default cannot be a string. Use bytes content "
                    "instead.",
                    obj=field,
                    id="fields.E170",
                ),
            ],
        )
def test_missing_max_length(self):
        class Model(models.Model):
            field = models.CharField()

        field = Model._meta.get_field("field")
        expected = (
            []
            if connection.features.supports_unlimited_charfield
            else [
                Error(
                    "CharFields must define a 'max_length' attribute.",
                    obj=field,
                    id="fields.E120",
                ),
            ]
        )
        self.assertEqual(field.check(), expected)
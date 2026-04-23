def test_decimal_places_greater_than_max_digits(self):
        class Model(models.Model):
            field = models.DecimalField(max_digits=9, decimal_places=10)

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'max_digits' must be greater or equal to 'decimal_places'.",
                    obj=field,
                    id="fields.E134",
                ),
            ],
        )
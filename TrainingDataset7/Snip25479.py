def test_bad_values_of_max_digits_and_decimal_places(self):
        class Model(models.Model):
            field = models.DecimalField(max_digits="bad", decimal_places="bad")

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(databases=self.databases),
            [
                Error(
                    "'decimal_places' must be a non-negative integer.",
                    obj=field,
                    id="fields.E131",
                ),
                Error(
                    "'max_digits' must be a positive integer.",
                    obj=field,
                    id="fields.E133",
                ),
            ],
        )
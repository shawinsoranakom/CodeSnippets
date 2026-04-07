def test_invalid_value(self):
        field = models.DecimalField(max_digits=4, decimal_places=2)
        msg = "“%s” value must be a decimal number."
        tests = [
            (),
            [],
            {},
            set(),
            object(),
            complex(),
            "non-numeric string",
            b"non-numeric byte-string",
        ]
        for value in tests:
            with self.subTest(value):
                with self.assertRaisesMessage(ValidationError, msg % (value,)):
                    field.clean(value, None)
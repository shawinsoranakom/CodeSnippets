def test_value_placeholder_with_decimal_field(self):
        cases = [
            ("NaN", "invalid"),
            ("123", "max_digits"),
            ("0.12", "max_decimal_places"),
            ("12", "max_whole_digits"),
        ]
        for value, code in cases:
            with self.subTest(value=value):

                class MyForm(forms.Form):
                    field = forms.DecimalField(
                        max_digits=2,
                        decimal_places=1,
                        error_messages={code: "%(value)s"},
                    )

                form = MyForm({"field": value})
                self.assertIs(form.is_valid(), False)
                self.assertEqual(form.errors, {"field": [value]})
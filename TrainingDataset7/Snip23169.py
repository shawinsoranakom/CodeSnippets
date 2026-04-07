def test_value_placeholder_with_integer_field(self):
        cases = [
            (validators.MaxValueValidator(0), 1, "max_value"),
            (validators.MinValueValidator(0), -1, "min_value"),
            (validators.URLValidator(), "1", "invalid"),
        ]
        for validator, value, code in cases:
            with self.subTest(type(validator).__name__, value=value):

                class MyForm(forms.Form):
                    field = forms.IntegerField(
                        validators=[validator],
                        error_messages={code: "%(value)s"},
                    )

                form = MyForm({"field": value})
                self.assertIs(form.is_valid(), False)
                self.assertEqual(form.errors, {"field": [str(value)]})
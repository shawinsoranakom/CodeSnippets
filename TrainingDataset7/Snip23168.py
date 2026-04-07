def test_value_placeholder_with_null_character(self):
        class MyForm(forms.Form):
            field = forms.CharField(
                error_messages={"null_characters_not_allowed": "%(value)s"},
            )

        form = MyForm({"field": "a\0b"})
        self.assertIs(form.is_valid(), False)
        self.assertEqual(form.errors, {"field": ["a\x00b"]})
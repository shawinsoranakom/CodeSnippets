def test_html_autocomplete_attributes(self):
        form = self.form_class()
        tests = (
            ("username", "username"),
            ("password1", "new-password"),
            ("password2", "new-password"),
        )
        for field_name, autocomplete in tests:
            with self.subTest(field_name=field_name, autocomplete=autocomplete):
                self.assertEqual(
                    form.fields[field_name].widget.attrs["autocomplete"], autocomplete
                )
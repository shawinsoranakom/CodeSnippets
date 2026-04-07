def test_html_autocomplete_attributes(self):
        form = AuthenticationForm()
        tests = (
            ("username", "username"),
            ("password", "current-password"),
        )
        for field_name, autocomplete in tests:
            with self.subTest(field_name=field_name, autocomplete=autocomplete):
                self.assertEqual(
                    form.fields[field_name].widget.attrs["autocomplete"], autocomplete
                )
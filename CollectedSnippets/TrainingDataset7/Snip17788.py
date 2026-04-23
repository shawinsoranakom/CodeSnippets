def test_html_autocomplete_attributes(self):
        form = SetPasswordForm(self.u1)
        tests = (
            ("new_password1", "new-password"),
            ("new_password2", "new-password"),
        )
        for field_name, autocomplete in tests:
            with self.subTest(field_name=field_name, autocomplete=autocomplete):
                self.assertEqual(
                    form.fields[field_name].widget.attrs["autocomplete"], autocomplete
                )
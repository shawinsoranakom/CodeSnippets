def test_form_fields(self):
        form = self.form_class()
        self.assertEqual(
            list(form.fields.keys()),
            ["username", "password1", "password2", "usable_password"],
        )
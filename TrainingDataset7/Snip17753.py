def test_username_field_autocapitalize_none(self):
        form = self.form_class()
        self.assertEqual(
            form.fields["username"].widget.attrs.get("autocapitalize"), "none"
        )
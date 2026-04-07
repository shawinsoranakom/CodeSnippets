def test_username_field_autocapitalize_none(self):
        form = AuthenticationForm()
        self.assertEqual(
            form.fields["username"].widget.attrs.get("autocapitalize"), "none"
        )
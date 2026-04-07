def test_username_field_autocapitalize_none(self):
        form = UserChangeForm()
        self.assertEqual(
            form.fields["username"].widget.attrs.get("autocapitalize"), "none"
        )
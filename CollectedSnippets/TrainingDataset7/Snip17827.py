def test_html_autocomplete_attributes(self):
        form = PasswordResetForm()
        self.assertEqual(form.fields["email"].widget.attrs["autocomplete"], "email")
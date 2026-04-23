def test_html_autocomplete_attributes(self):
        user = User.objects.get(username="testclient")
        form = PasswordChangeForm(user)
        self.assertEqual(
            form.fields["old_password"].widget.attrs["autocomplete"], "current-password"
        )
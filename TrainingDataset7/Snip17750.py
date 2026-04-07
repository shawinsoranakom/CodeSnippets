def test_password_help_text(self):
        form = self.form_class()
        self.assertEqual(
            form.fields["password1"].help_text,
            "<ul><li>"
            "Your password can’t be too similar to your other personal information."
            "</li></ul>",
        )
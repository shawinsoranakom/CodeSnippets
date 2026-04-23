def test_flatpage_requires_trailing_slash_with_append_slash(self):
        form = FlatpageForm(data=dict(url="/no_trailing_slash", **self.form_data))
        with translation.override("en"):
            self.assertEqual(
                form.fields["url"].help_text,
                "Example: “/about/contact/”. Make sure to have leading and "
                "trailing slashes.",
            )
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["url"], ["URL is missing a trailing slash."])
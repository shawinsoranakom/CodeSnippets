def test_flatpage_doesnt_requires_trailing_slash_without_append_slash(self):
        form = FlatpageForm(data=dict(url="/no_trailing_slash", **self.form_data))
        self.assertTrue(form.is_valid())
        with translation.override("en"):
            self.assertEqual(
                form.fields["url"].help_text,
                "Example: “/about/contact”. Make sure to have a leading slash.",
            )
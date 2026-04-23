def test_flatpage_requires_leading_slash(self):
        form = FlatpageForm(data=dict(url="no_leading_slash/", **self.form_data))
        with translation.override("en"):
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["url"], ["URL is missing a leading slash."])
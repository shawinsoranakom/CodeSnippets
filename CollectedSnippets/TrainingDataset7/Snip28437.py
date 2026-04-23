def test_https_prefixing(self):
        """
        If the https:// prefix is omitted on form input, the field adds it
        again.
        """

        class HomepageForm(forms.ModelForm):
            class Meta:
                model = Homepage
                fields = "__all__"

        form = HomepageForm({"url": "example.com"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["url"], "https://example.com")

        form = HomepageForm({"url": "example.com/test"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["url"], "https://example.com/test")
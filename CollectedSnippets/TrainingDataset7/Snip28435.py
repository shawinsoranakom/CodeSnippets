def test_url_on_modelform(self):
        "Check basic URL field validation on model forms"

        class HomepageForm(forms.ModelForm):
            class Meta:
                model = Homepage
                fields = "__all__"

        self.assertFalse(HomepageForm({"url": "foo"}).is_valid())
        self.assertFalse(HomepageForm({"url": "http://"}).is_valid())
        self.assertFalse(HomepageForm({"url": "http://example"}).is_valid())
        self.assertFalse(HomepageForm({"url": "http://example."}).is_valid())
        self.assertFalse(HomepageForm({"url": "http://com."}).is_valid())

        self.assertTrue(HomepageForm({"url": "http://localhost"}).is_valid())
        self.assertTrue(HomepageForm({"url": "http://example.com"}).is_valid())
        self.assertTrue(HomepageForm({"url": "http://www.example.com"}).is_valid())
        self.assertTrue(HomepageForm({"url": "http://www.example.com:8000"}).is_valid())
        self.assertTrue(HomepageForm({"url": "http://www.example.com/test"}).is_valid())
        self.assertTrue(
            HomepageForm({"url": "http://www.example.com:8000/test"}).is_valid()
        )
        self.assertTrue(HomepageForm({"url": "http://example.com/foo/bar"}).is_valid())
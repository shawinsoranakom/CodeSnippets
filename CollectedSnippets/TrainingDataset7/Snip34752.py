def test_nontext_not_contains(self):
        r = self.client.get("/no_template_view/")
        self.assertNotContains(r, gettext_lazy("never"))
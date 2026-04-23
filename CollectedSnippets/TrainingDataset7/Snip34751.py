def test_nontext_contains(self):
        r = self.client.get("/no_template_view/")
        self.assertContains(r, gettext_lazy("once"))
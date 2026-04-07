def test_templatetag_index(self):
        # Overridden because non-trivial TEMPLATES settings aren't supported
        # but the page shouldn't crash (#24125).
        response = self.client.get(reverse("django-admindocs-tags"))
        self.assertContains(response, "<title>Template tags</title>", html=True)
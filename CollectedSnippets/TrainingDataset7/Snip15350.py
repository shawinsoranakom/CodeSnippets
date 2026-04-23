def test_templatefilter_index(self):
        # Overridden because non-trivial TEMPLATES settings aren't supported
        # but the page shouldn't crash (#24125).
        response = self.client.get(reverse("django-admindocs-filters"))
        self.assertContains(response, "<title>Template filters</title>", html=True)
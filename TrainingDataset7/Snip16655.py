def test_filters(self):
        response = self.client.get(reverse("django-admindocs-filters"))

        # The builtin filter group exists
        self.assertContains(response, "<h2>Built-in filters</h2>", count=2, html=True)

        # A builtin filter exists in both the index and detail
        self.assertContains(response, '<h3 id="built_in-add">add</h3>', html=True)
        self.assertContains(
            response, '<li><a href="#built_in-add">add</a></li>', html=True
        )
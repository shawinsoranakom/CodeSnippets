def test_index_headers(self):
        response = self.client.get(reverse("django-admindocs-docroot"))
        self.assertContains(response, "<h1>Documentation</h1>")
        self.assertContains(response, '<h2><a href="tags/">Tags</a></h2>')
        self.assertContains(response, '<h2><a href="filters/">Filters</a></h2>')
        self.assertContains(response, '<h2><a href="models/">Models</a></h2>')
        self.assertContains(response, '<h2><a href="views/">Views</a></h2>')
        self.assertContains(
            response, '<h2><a href="bookmarklets/">Bookmarklets</a></h2>'
        )
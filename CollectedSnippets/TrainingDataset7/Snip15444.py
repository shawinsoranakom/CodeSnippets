def test_facets_always(self):
        modeladmin = DecadeFilterBookAdminWithAlwaysFacets(Book, site)
        request = self.request_factory.get("/")
        self._test_facets(modeladmin, request)
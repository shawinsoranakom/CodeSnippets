def test_facets_no_filter(self):
        modeladmin = DecadeFilterBookAdmin(Book, site)
        request = self.request_factory.get("/?_facets")
        self._test_facets(modeladmin, request, query_string="_facets")
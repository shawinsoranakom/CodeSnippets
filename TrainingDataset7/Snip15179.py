def test_search_role(self):
        m = BandAdmin(Band, custom_site)
        m.search_fields = ["name"]
        request = self._mocked_authenticated_request("/band/", self.superuser)
        response = m.changelist_view(request)
        self.assertContains(
            response,
            '<h2 id="changelist-search-form" class="visually-hidden">Search bands</h2>',
        )
        self.assertContains(
            response,
            '<form id="changelist-search" method="get" role="search" '
            'aria-labelledby="changelist-search-form">',
        )
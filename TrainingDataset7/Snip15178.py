def test_search_help_text(self):
        superuser = self._create_superuser("superuser")
        m = BandAdmin(Band, custom_site)
        # search_fields without search_help_text.
        m.search_fields = ["name"]
        request = self._mocked_authenticated_request("/band/", superuser)
        response = m.changelist_view(request)
        self.assertIsNone(response.context_data["cl"].search_help_text)
        self.assertNotContains(response, '<div class="help id="searchbar_helptext">')
        # search_fields with search_help_text.
        m.search_help_text = "Search help text"
        request = self._mocked_authenticated_request("/band/", superuser)
        response = m.changelist_view(request)
        self.assertEqual(
            response.context_data["cl"].search_help_text, "Search help text"
        )
        self.assertContains(
            response, '<div class="help" id="searchbar_helptext">Search help text</div>'
        )
        self.assertContains(
            response,
            '<input type="text" size="40" name="q" value="" id="searchbar" '
            'aria-describedby="searchbar_helptext">',
        )
def test_dynamic_search_fields(self):
        child = self._create_superuser("child")
        m = DynamicSearchFieldsChildAdmin(Child, custom_site)
        request = self._mocked_authenticated_request("/child/", child)
        response = m.changelist_view(request)
        self.assertEqual(response.context_data["cl"].search_fields, ("name", "age"))
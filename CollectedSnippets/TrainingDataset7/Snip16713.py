def test_all_fields_hidden(self):
        response = self.client.get(reverse("admin:admin_views_emptymodelhidden_add"))
        self.assert_fieldline_hidden(response)
        self.assert_field_hidden(response, "first")
        self.assert_field_hidden(response, "second")
def test_all_fields_visible(self):
        response = self.client.get(reverse("admin:admin_views_emptymodelvisible_add"))
        self.assert_fieldline_visible(response)
        self.assert_field_visible(response, "first")
        self.assert_field_visible(response, "second")
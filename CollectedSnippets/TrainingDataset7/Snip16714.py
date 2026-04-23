def test_mixin(self):
        response = self.client.get(reverse("admin:admin_views_emptymodelmixin_add"))
        self.assert_fieldline_visible(response)
        self.assert_field_hidden(response, "first")
        self.assert_field_visible(response, "second")
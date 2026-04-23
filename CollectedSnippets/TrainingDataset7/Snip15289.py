def test_add_with_GET_args(self):
        """
        Ensure GET on the add_view plus specifying a field value in the query
        string works.
        """
        response = self.client.get(
            reverse("admin_custom_urls:admin_custom_urls_action_add"),
            {"name": "My Action"},
        )
        self.assertContains(response, 'value="My Action"')
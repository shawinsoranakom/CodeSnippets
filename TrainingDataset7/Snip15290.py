def test_basic_add_POST(self):
        """
        Ensure POST on add_view works.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            "name": "Action added through a popup",
            "description": "Description of added action",
        }
        response = self.client.post(
            reverse("admin_custom_urls:admin_custom_urls_action_add"), post_data
        )
        self.assertContains(response, "Action added through a popup")
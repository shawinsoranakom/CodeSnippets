def test_popup_add_POST(self):
        """HTTP response from a popup is properly escaped."""
        post_data = {
            IS_POPUP_VAR: "1",
            "title": "title with a new\nline",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        response = self.client.post(reverse("admin:admin_views_article_add"), post_data)
        self.assertContains(response, "title with a new\\nline")
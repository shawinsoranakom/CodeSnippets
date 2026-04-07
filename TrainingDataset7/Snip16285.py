def test_popup_add_POST_with_valid_source_model(self):
        """
        Popup add with a valid source_model returns a successful response.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            SOURCE_MODEL_VAR: "admin_views.section",
            "title": "Test Article",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        response = self.client.post(reverse("admin:admin_views_article_add"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-popup-response")
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)
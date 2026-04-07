def test_popup_add_POST_with_invalid_source_model(self):
        """
        Popup add with an invalid source_model (non-existent app/model)
        shows an error message instead of crashing.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            SOURCE_MODEL_VAR: "admin_views.nonexistent",
            "title": "Test Article",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        response = self.client.post(reverse("admin:admin_views_article_add"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-popup-response")
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn("admin_views.nonexistent", str(messages[0]))
        self.assertIn("could not be found", str(messages[0]))
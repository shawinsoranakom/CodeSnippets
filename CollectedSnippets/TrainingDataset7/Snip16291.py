def test_popup_add_POST_with_unregistered_source_model(self):
        """
        Popup add where source_model is a valid Django model but is not
        registered in the admin site (e.g. a model only used as an inline)
        should succeed without raising a KeyError.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            # Chapter exists as a model but is not registered in site (only
            # in site6), simulating a model used only as an inline.
            SOURCE_MODEL_VAR: "admin_views.chapter",
            "title": "Test Article",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        response = self.client.post(reverse("admin:admin_views_article_add"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-popup-response")
        # No error messages - unregistered model is silently skipped.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)
        # No optgroup in the response.
        self.assertNotContains(response, "&quot;optgroup&quot;")
def test_popup_add_POST_without_optgroups(self):
        """
        Popup add where source_model form exists but doesn't have the field
        should work without crashing.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            SOURCE_MODEL_VAR: "admin_views.section",
            "title": "Test Article 2",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        # Use regular admin (not admin11) where Section doesn't have optgroups.
        response = self.client.post(reverse("admin:admin_views_article_add"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-popup-response")
        self.assertNotContains(response, "&quot;optgroup&quot;")
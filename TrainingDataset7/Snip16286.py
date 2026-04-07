def test_popup_add_POST_with_optgroups(self):
        """
        Popup add with source_model containing optgroup choices includes
        the optgroup in the response.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            SOURCE_MODEL_VAR: "admin_views.section",
            "title": "Test Article",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        response = self.client.post(
            reverse("admin11:admin_views_article_add"), post_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&quot;optgroup&quot;: &quot;Published&quot;")
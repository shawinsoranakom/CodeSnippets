def test_popup_add_POST_with_dynamic_optgroups(self):
        """
        Popup add with source_model where optgroup field is added dynamically
        in __init__. This ensures the implementation doesn't rely on accessing
        the uninstantiated form class's _meta or fields, but instead properly
        instantiates the form with get_form(request)() to access field info.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            SOURCE_MODEL_VAR: "admin_views.section",
            "title": "Item 1",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        response = self.client.post(
            reverse("admin13:admin_views_article_add"), post_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&quot;optgroup&quot;: &quot;Category A&quot;")
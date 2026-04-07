def test_popup_add_POST_with_object_optgroups(self):
        """
        Popup add with source_model containing optgroups where the optgroup
        keys are model instances (not strings) still serialize to strings.
        """
        post_data = {
            IS_POPUP_VAR: "1",
            SOURCE_MODEL_VAR: "admin_views.section",
            "title": "Article 1",
            "content": "some content",
            "date_0": "2010-09-10",
            "date_1": "14:55:39",
        }
        response = self.client.post(
            reverse("admin12:admin_views_article_add"), post_data
        )
        self.assertEqual(response.status_code, 200)
        # Check that optgroup is in the response with str() of Section instance
        # The form uses Section.objects.all()[:2] which includes cls.s1
        # ("Test section") as the first optgroup key (HTML encoded).
        self.assertContains(response, "&quot;optgroup&quot;: &quot;Test section&quot;")
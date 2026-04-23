def test_edit_save_as(self):
        """
        Test "save as".
        """
        post_data = self.inline_post_data.copy()
        post_data.update(
            {
                "_saveasnew": "Save+as+new",
                "article_set-1-section": "1",
                "article_set-2-section": "1",
                "article_set-3-section": "1",
                "article_set-4-section": "1",
                "article_set-5-section": "1",
            }
        )
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), post_data
        )
        self.assertEqual(response.status_code, 302)
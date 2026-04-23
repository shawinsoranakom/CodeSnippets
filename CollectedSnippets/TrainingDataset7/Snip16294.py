def test_edit_save_as_delete_inline(self):
        """
        Should be able to "Save as new" while also deleting an inline.
        """
        post_data = self.inline_post_data.copy()
        post_data.update(
            {
                "_saveasnew": "Save+as+new",
                "article_set-1-section": "1",
                "article_set-2-section": "1",
                "article_set-2-DELETE": "1",
                "article_set-3-section": "1",
            }
        )
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), post_data
        )
        self.assertEqual(response.status_code, 302)
        # started with 3 articles, one was deleted.
        self.assertEqual(Section.objects.latest("id").article_set.count(), 2)
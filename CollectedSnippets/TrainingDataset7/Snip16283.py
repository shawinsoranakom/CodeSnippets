def test_basic_add_POST(self):
        """
        A smoke test to ensure POST on add_view works.
        """
        post_data = {
            "name": "Another Section",
            # inline data
            "article_set-TOTAL_FORMS": "3",
            "article_set-INITIAL_FORMS": "0",
            "article_set-MAX_NUM_FORMS": "0",
        }
        response = self.client.post(reverse("admin:admin_views_section_add"), post_data)
        self.assertEqual(response.status_code, 302)
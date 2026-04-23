def test_basic_add_POST(self):
        """
        A smoke test to ensure POST on add_view works.
        """
        post_data = {
            "name": "This Week in Django",
            # inline data
            "generic_inline_admin-media-content_type-object_id-TOTAL_FORMS": "1",
            "generic_inline_admin-media-content_type-object_id-INITIAL_FORMS": "0",
            "generic_inline_admin-media-content_type-object_id-MAX_NUM_FORMS": "0",
        }
        response = self.client.post(
            reverse("admin:generic_inline_admin_episode_add"), post_data
        )
        self.assertEqual(response.status_code, 302)
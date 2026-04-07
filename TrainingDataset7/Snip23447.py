def test_basic_edit_POST(self):
        """
        A smoke test to ensure POST on edit_view works.
        """
        prefix = "generic_inline_admin-media-content_type-object_id"
        post_data = {
            "name": "This Week in Django",
            # inline data
            f"{prefix}-TOTAL_FORMS": "3",
            f"{prefix}-INITIAL_FORMS": "2",
            f"{prefix}-MAX_NUM_FORMS": "0",
            f"{prefix}-0-id": str(self.mp3_media_pk),
            f"{prefix}-0-url": "http://example.com/podcast.mp3",
            f"{prefix}-1-id": str(self.png_media_pk),
            f"{prefix}-1-url": "http://example.com/logo.png",
            f"{prefix}-2-id": "",
            f"{prefix}-2-url": "",
        }
        url = reverse(
            "admin:generic_inline_admin_episode_change", args=(self.episode_pk,)
        )
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
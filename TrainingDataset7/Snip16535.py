def test_inline_file_upload_edit_validation_error_post(self):
        """
        Inline file uploads correctly display prior data (#10002).
        """
        post_data = {
            "name": "Test Gallery",
            "pictures-TOTAL_FORMS": "2",
            "pictures-INITIAL_FORMS": "1",
            "pictures-MAX_NUM_FORMS": "0",
            "pictures-0-id": str(self.picture.id),
            "pictures-0-gallery": str(self.gallery.id),
            "pictures-0-name": "Test Picture",
            "pictures-0-image": "",
            "pictures-1-id": "",
            "pictures-1-gallery": str(self.gallery.id),
            "pictures-1-name": "Test Picture 2",
            "pictures-1-image": "",
        }
        response = self.client.post(
            reverse("admin:admin_views_gallery_change", args=(self.gallery.id,)),
            post_data,
        )
        self.assertContains(response, b"Currently")
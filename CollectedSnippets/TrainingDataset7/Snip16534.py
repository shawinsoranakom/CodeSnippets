def test_form_has_multipart_enctype(self):
        response = self.client.get(
            reverse("admin:admin_views_gallery_change", args=(self.gallery.id,))
        )
        self.assertIs(response.context["has_file_field"], True)
        self.assertContains(response, MULTIPART_ENCTYPE)
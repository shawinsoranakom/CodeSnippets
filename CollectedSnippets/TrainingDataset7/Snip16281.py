def test_basic_edit_GET_old_url_redirect(self):
        """
        The change URL changed in Django 1.9, but the old one still redirects.
        """
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)).replace(
                "change/", ""
            )
        )
        self.assertRedirects(
            response, reverse("admin:admin_views_section_change", args=(self.s1.pk,))
        )
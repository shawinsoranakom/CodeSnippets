def test_display_consecutive_whitespace_object_in_changelist(self):
        response = self.client.get(reverse("admin:admin_views_coverletter_changelist"))
        self.assertContains(response, f'<a href="{self.change_link}">-</a>')
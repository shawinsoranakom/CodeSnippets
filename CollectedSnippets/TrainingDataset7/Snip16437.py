def test_display_consecutive_whitespace_object_in_sub_title(self):
        response = self.client.get(self.change_link)
        self.assertContains(response, "<h2>-</h2>")
        response = self.client.get(
            reverse("admin:admin_views_coverletter_history", args=(self.obj.pk,))
        )
        self.assertContains(response, "<h1>Change history: -</h1>")
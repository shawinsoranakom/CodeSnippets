def test_breadcrumbs_present(self):
        response = self.client.get(reverse("admin:auth_user_add"))
        self.assertContains(response, '<nav aria-label="Breadcrumbs">')
        response = self.client.get(
            reverse("admin:app_list", kwargs={"app_label": "auth"})
        )
        self.assertContains(response, '<nav aria-label="Breadcrumbs">')
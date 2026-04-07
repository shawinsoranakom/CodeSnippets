def test_custom_admin_site_logout_template(self):
        response = self.client.post(reverse("admin2:logout"))
        self.assertIsInstance(response, TemplateResponse)
        self.assertTemplateUsed(response, "custom_admin/logout.html")
        self.assertContains(response, "Hello from a custom logout template")
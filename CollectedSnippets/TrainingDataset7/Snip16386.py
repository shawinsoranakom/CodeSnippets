def test_custom_admin_site_login_template(self):
        self.client.logout()
        response = self.client.get(reverse("admin2:index"), follow=True)
        self.assertIsInstance(response, TemplateResponse)
        self.assertTemplateUsed(response, "custom_admin/login.html")
        self.assertContains(response, "Hello from a custom login template")
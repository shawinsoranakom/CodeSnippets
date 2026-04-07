def test_custom_admin_site_password_change_done_template(self):
        response = self.client.get(reverse("admin2:password_change_done"))
        self.assertIsInstance(response, TemplateResponse)
        self.assertTemplateUsed(response, "custom_admin/password_change_done.html")
        self.assertContains(
            response, "Hello from a custom password change done template"
        )
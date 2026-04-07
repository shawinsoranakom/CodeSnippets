def test_custom_admin_site_index_view_and_template(self):
        response = self.client.get(reverse("admin2:index"))
        self.assertIsInstance(response, TemplateResponse)
        self.assertTemplateUsed(response, "custom_admin/index.html")
        self.assertContains(response, "Hello from a custom index template *bar*")
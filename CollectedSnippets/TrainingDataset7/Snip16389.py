def test_custom_admin_site_app_index_view_and_template(self):
        response = self.client.get(reverse("admin2:app_list", args=("admin_views",)))
        self.assertIsInstance(response, TemplateResponse)
        self.assertTemplateUsed(response, "custom_admin/app_index.html")
        self.assertContains(response, "Hello from a custom app_index template")
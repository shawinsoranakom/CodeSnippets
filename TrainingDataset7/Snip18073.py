def test_admin_path(self):
        admin_url = reverse("admin:index")
        response = self.client.get(admin_url)
        self.assertRedirects(
            response,
            reverse("admin:login") + f"?next={admin_url}",
            target_status_code=200,
        )
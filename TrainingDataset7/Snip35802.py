def test_user_permission_with_lazy_reverse(self):
        alfred = User.objects.create_user(
            "alfred", "alfred@example.com", password="testpw"
        )
        response = self.client.get("/login_required_view/")
        self.assertRedirects(
            response, "/login/?next=/login_required_view/", status_code=302
        )
        self.client.force_login(alfred)
        response = self.client.get("/login_required_view/")
        self.assertEqual(response.status_code, 200)
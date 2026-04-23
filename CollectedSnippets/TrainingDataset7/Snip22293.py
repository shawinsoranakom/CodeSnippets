def test_view_authenticated_flatpage(self):
        "A flatpage served through a view can require authentication"
        response = self.client.get("/flatpage_root/sekrit/")
        self.assertRedirects(response, "/accounts/login/?next=/flatpage_root/sekrit/")
        user = User.objects.create_user("testuser", "test@example.com", "s3krit")
        self.client.force_login(user)
        response = self.client.get("/flatpage_root/sekrit/")
        self.assertContains(response, "<p>Isn't it sekrit!</p>")
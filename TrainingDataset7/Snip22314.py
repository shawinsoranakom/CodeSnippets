def test_fallback_authenticated_flatpage(self):
        "A flatpage served by the middleware can require authentication"
        response = self.client.get("/sekrit/")
        self.assertRedirects(response, "/accounts/login/?next=/sekrit/")
        user = User.objects.create_user("testuser", "test@example.com", "s3krit")
        self.client.force_login(user)
        response = self.client.get("/sekrit/")
        self.assertContains(response, "<p>Isn't it sekrit!</p>")
def test_confirm_invalid_user(self):
        # A nonexistent user returns a 200 response, not a 404.
        response = self.client.get("/reset/123456/1-1/")
        self.assertContains(response, "The password reset link was invalid")
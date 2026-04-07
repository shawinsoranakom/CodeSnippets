def test_redirect_fallback_non_existent_flatpage(self):
        """
        A nonexistent flatpage won't be served if the fallback middleware is
        disabled and should not add a slash.
        """
        response = self.client.get("/no_such_flatpage")
        self.assertEqual(response.status_code, 404)
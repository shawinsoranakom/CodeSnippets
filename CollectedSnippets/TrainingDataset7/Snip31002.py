def test_redirect_not_found_with_append_slash(self):
        """
        Exercise the second Redirect.DoesNotExist branch in
        RedirectFallbackMiddleware.
        """
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 404)
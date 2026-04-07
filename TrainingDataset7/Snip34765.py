def test_incorrect_target(self):
        "An assertion is raised if the response redirects to another target"
        response = self.client.get("/permanent_redirect_view/")
        msg = (
            "Response didn't redirect as expected: Response code was 301 (expected 302)"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            # Should redirect to get_view
            self.assertRedirects(response, "/some_view/")
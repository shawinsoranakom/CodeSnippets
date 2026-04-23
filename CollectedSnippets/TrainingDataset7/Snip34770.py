def test_redirect_chain_to_self(self):
        "Redirections to self are caught and escaped"
        with self.assertRaises(RedirectCycleError) as context:
            self.client.get("/redirect_to_self/", {}, follow=True)
        response = context.exception.last_response
        # The chain of redirects stops once the cycle is detected.
        self.assertRedirects(
            response, "/redirect_to_self/", status_code=302, target_status_code=302
        )
        self.assertEqual(len(response.redirect_chain), 2)
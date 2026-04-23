def test_circular_redirect(self):
        "Circular redirect chains are caught and escaped"
        with self.assertRaises(RedirectCycleError) as context:
            self.client.get("/circular_redirect_1/", {}, follow=True)
        response = context.exception.last_response
        # The chain of redirects will get back to the starting point, but stop
        # there.
        self.assertRedirects(
            response, "/circular_redirect_2/", status_code=302, target_status_code=302
        )
        self.assertEqual(len(response.redirect_chain), 4)
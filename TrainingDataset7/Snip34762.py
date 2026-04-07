def test_followed_redirect_unexpected_initial_status_code(self):
        response = self.client.get("/permanent_redirect_view/", follow=True)
        msg = (
            "Initial response didn't redirect as expected: Response code was 301 "
            "(expected 302)"
        )
        self.assertRaisesPrefixedMessage(
            self.assertRedirects,
            response,
            "/get_view/",
            expected_msg=msg,
        )
def test_followed_redirect_unexpected_final_status_code(self):
        response = self.client.get("/redirect_view/", follow=True)
        msg = (
            "Response didn't redirect as expected: Final Response code was 200 "
            "(expected 403)"
        )
        self.assertRaisesPrefixedMessage(
            self.assertRedirects,
            response,
            "/get_view/",
            status_code=302,
            target_status_code=403,
            expected_msg=msg,
        )
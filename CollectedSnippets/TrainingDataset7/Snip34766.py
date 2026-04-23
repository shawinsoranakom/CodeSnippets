def test_target_page(self):
        """
        An assertion is raised if the response redirect target cannot be
        retrieved as expected.
        """
        response = self.client.get("/double_redirect_view/")
        msg = (
            "Couldn't retrieve redirection page '/permanent_redirect_view/': "
            "response code was 301 (expected 200)"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            # The redirect target responds with a 301 code, not 200
            self.assertRedirects(response, "http://testserver/permanent_redirect_view/")

        msg = (
            "abc: Couldn't retrieve redirection page '/permanent_redirect_view/': "
            "response code was 301 (expected 200)"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            # The redirect target responds with a 301 code, not 200
            self.assertRedirects(
                response, "http://testserver/permanent_redirect_view/", msg_prefix="abc"
            )
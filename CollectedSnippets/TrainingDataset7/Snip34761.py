def test_redirect_page(self):
        """
        An assertion is raised if the original page couldn't be retrieved as
        expected
        """
        # This page will redirect with code 301, not 302
        response = self.client.get("/permanent_redirect_view/")
        msg = (
            "Response didn't redirect as expected: Response code was 301 "
            "(expected 302)"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertRedirects(response, "/get_view/")

        msg = (
            "abc: Response didn't redirect as expected: Response code was 301 "
            "(expected 302)"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertRedirects(response, "/get_view/", msg_prefix="abc")
def test_lost_query(self):
        """
        An assertion is raised if the redirect location doesn't preserve GET
        parameters.
        """
        response = self.client.get("/redirect_view/", {"var": "value"})
        msg = "Response redirected to '/get_view/?var=value', expected '/get_view/'"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertRedirects(response, "/get_view/")

        msg = (
            "abc: Response redirected to '/get_view/?var=value', expected '/get_view/'"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertRedirects(response, "/get_view/", msg_prefix="abc")
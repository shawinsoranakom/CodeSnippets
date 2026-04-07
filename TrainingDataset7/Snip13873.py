def assertNotContains(
        self, response, text, status_code=200, msg_prefix="", html=False
    ):
        """
        Assert that a response indicates that some content was retrieved
        successfully, (i.e., the HTTP status code was as expected) and that
        ``text`` doesn't occur in the content of the response.
        """
        real_count, msg_prefix, response_content = self._assert_contains(
            response, text, status_code, msg_prefix, html
        )

        if real_count != 0:
            text_repr = self._text_repr(text, force_string=html)
            self.fail(
                f"{real_count} != 0 :{msg_prefix}{text_repr} unexpectedly found in the "
                f"following response\n{response_content!r}"
            )
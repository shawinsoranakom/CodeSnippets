def assertContains(
        self, response, text, count=None, status_code=200, msg_prefix="", html=False
    ):
        """
        Assert that a response indicates that some content was retrieved
        successfully, (i.e., the HTTP status code was as expected) and that
        ``text`` occurs ``count`` times in the content of the response.
        If ``count`` is None, the count doesn't matter - the assertion is true
        if the text occurs at least once in the response.
        """
        real_count, msg_prefix, response_content = self._assert_contains(
            response, text, status_code, msg_prefix, html
        )

        if (count is None and real_count > 0) or (
            (count is not None and real_count == count)
        ):
            return

        text_repr = self._text_repr(text, force_string=html)

        if count is not None:
            msg = (
                f"{real_count} != {count} : {msg_prefix}Found {real_count} instances "
                f"of {text_repr} (expected {count}) in the following response\n"
                f"{response_content!r}"
            )
        else:
            msg = (
                f"False is not true : {msg_prefix}Couldn't find {text_repr} in the "
                f"following response\n{response_content!r}"
            )
        self.fail(msg)
def assertRaisesPrefixedMessage(
        self,
        method,
        *method_args,
        expected_msg,
        msg_prefix="abc",
        **method_kwargs,
    ):
        """
        `method` raises an AssertionError with and without a prefixed message.

        :param method: The assertion method to test.
        :param method_args: Positional arguments to pass to the method.
        :param expected_msg: The expected base error message (required
                             keyword-only).
        :param msg_prefix: Optional prefix to be added to the message in the
                           second subTest.
        :param method_kwargs: Keyword arguments to pass to the method.

        Used internally for testing Django's assertions.
        """
        with (
            self.subTest("without prefix"),
            self.assertRaisesMessage(AssertionError, expected_msg),
        ):
            method(*method_args, **method_kwargs)

        with (
            self.subTest("with prefix"),
            self.assertRaisesMessage(AssertionError, f"{msg_prefix}: {expected_msg}"),
        ):
            method(*method_args, **method_kwargs, msg_prefix=msg_prefix)
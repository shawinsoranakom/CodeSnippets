def assertRaisesMessage(
        self, expected_exception, expected_message, *args, **kwargs
    ):
        """
        Assert that expected_message is found in the message of a raised
        exception.

        Args:
            expected_exception: Exception class expected to be raised.
            expected_message: expected error message string value.
            args: Function to be called and extra positional args.
            kwargs: Extra kwargs.
        """
        return self._assertFooMessage(
            self.assertRaises,
            "exception",
            expected_exception,
            expected_message,
            *args,
            **kwargs,
        )
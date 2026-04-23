def assertMessageHasHeaders(self, message, headers):
        """
        Asserts that the `message` has all `headers`.

        message: can be an instance of an email.Message subclass or bytes
                 with the contents of an email message.
        headers: should be a set of (header-name, header-value) tuples.
        """
        if isinstance(message, bytes):
            message = message_from_bytes(message)
        msg_headers = set(message.items())
        if not headers.issubset(msg_headers):
            missing = "\n".join(f"  {h}: {v}" for h, v in headers - msg_headers)
            actual = "\n".join(f"  {h}: {v}" for h, v in msg_headers)
            raise self.failureException(
                f"Expected headers not found in message.\n"
                f"Missing headers:\n{missing}\n"
                f"Actual headers:\n{actual}"
            )
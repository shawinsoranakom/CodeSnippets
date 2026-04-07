def test_force_bytes_exception(self):
        """
        force_bytes knows how to convert to bytes an exception
        containing non-ASCII characters in its args.
        """
        error_msg = "This is an exception, voilà"
        exc = ValueError(error_msg)
        self.assertEqual(force_bytes(exc), error_msg.encode())
        self.assertEqual(
            force_bytes(exc, encoding="ascii", errors="ignore"),
            b"This is an exception, voil",
        )
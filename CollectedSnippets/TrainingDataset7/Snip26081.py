def test_nonascii_as_string_with_ascii_charset(self, mock_set_payload):
        """Line length check should encode the payload supporting
        `surrogateescape`.

        Following https://github.com/python/cpython/issues/76511, newer
        versions of Python (3.12.3 and 3.13+) ensure that a message's
        payload is encoded with the provided charset and `surrogateescape` is
        used as the error handling strategy.

        This test is heavily based on the test from the fix for the bug above.
        Line length checks in SafeMIMEText's set_payload should also use the
        same error handling strategy to avoid errors such as:

        UnicodeEncodeError: 'utf-8' codec can't encode <...>: surrogates not
        allowed

        """
        # This test is specific to Python's legacy MIMEText. This can be safely
        # removed when EmailMessage.message() uses Python's modern email API.
        # (Using surrogateescape for non-utf8 is covered in test_encoding().)
        from django.core.mail import SafeMIMEText

        def simplified_set_payload(instance, payload, charset):
            instance._payload = payload

        mock_set_payload.side_effect = simplified_set_payload

        text = (
            "Text heavily based in Python's text for non-ascii messages: Föö bär"
        ).encode("iso-8859-1")
        body = text.decode("ascii", errors="surrogateescape")
        message = SafeMIMEText(body, "plain", "ascii")
        mock_set_payload.assert_called_once()
        self.assertEqual(message.get_payload(decode=True), text)
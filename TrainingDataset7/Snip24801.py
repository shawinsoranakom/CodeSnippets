def test_encoded_with_newlines_in_headers(self):
        """
        Keys & values which throw a UnicodeError when encoding/decoding should
        still be checked for newlines and re-raised as a BadHeaderError.
        These specifically would still throw BadHeaderError after decoding
        successfully, because the newlines are sandwiched in the middle of the
        string and email.Header leaves those as they are.
        """
        r = HttpResponse()
        pairs = (
            ("†\nother", "test"),
            ("test", "†\nother"),
            (b"\xe2\x80\xa0\nother", "test"),
            ("test", b"\xe2\x80\xa0\nother"),
        )
        msg = "Header values can't contain newlines"
        for key, value in pairs:
            with self.subTest(key=key, value=value):
                with self.assertRaisesMessage(BadHeaderError, msg):
                    r[key] = value
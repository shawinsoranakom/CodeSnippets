def test_no_match(self):
        tests = [
            # other is falsey.
            ("*/*", None),
            ("*/*", ""),
            # other is malformed.
            ("*/*", "; q=0.8"),
            # main_type is falsey.
            ("/*", "*/*"),
            # other.main_type is falsey.
            ("*/*", "/*"),
            # main sub_type is falsey.
            ("application", "application/*"),
            # other.sub_type is falsey.
            ("application/*", "application"),
            # All main and sub types are defined, but there is no match.
            ("application/xml", "application/html"),
            ("text/vcard; version=4.0", "text/vcard; version=3.0"),
            ("text/vcard; q=0.7", "text/vcard; version=3.0"),
            ("text/vcard", "text/vcard; version=3.0"),
        ]
        for accepted_type, mime_type in tests:
            with self.subTest(accepted_type, mime_type=mime_type):
                self.assertIs(MediaType(accepted_type).match(mime_type), False)
def test_match(self):
        tests = [
            ("*/*; q=0.8", "*/*"),
            ("*/*", "application/json"),
            (" */* ", "application/json"),
            ("application/*", "application/json"),
            ("application/*", "application/*"),
            ("application/xml", "application/xml"),
            (" application/xml ", "application/xml"),
            ("application/xml", " application/xml "),
            ("text/vcard; version=4.0", "text/vcard; version=4.0"),
            ("text/vcard; version=4.0; q=0.7", "text/vcard; version=4.0"),
            ("text/vcard; version=4.0", "text/vcard"),
        ]
        for accepted_type, mime_type in tests:
            with self.subTest(accepted_type, mime_type=mime_type):
                self.assertIs(MediaType(accepted_type).match(mime_type), True)
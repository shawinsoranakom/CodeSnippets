def test_accept_with_param(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = "text/vcard; version=3.0, text/html;q=0.5"

        for media_types, expected in [
            (
                [
                    "text/vcard; version=4.0",
                    "text/vcard; version=3.0",
                    "text/vcard",
                    "text/directory",
                ],
                "text/vcard; version=3.0",
            ),
            (["text/vcard; version=4.0", "text/vcard", "text/directory"], None),
            (["text/vcard; version=4.0", "text/html"], "text/html"),
        ]:
            self.assertEqual(request.get_preferred_type(media_types), expected)
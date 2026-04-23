def test_accept_header_priority(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = (
            "text/html,application/xml;q=0.9,*/*;q=0.1,text/*;q=0.5"
        )

        tests = [
            (["text/html", "application/xml"], "text/html"),
            (["application/xml", "application/json"], "application/xml"),
            (["application/json"], "application/json"),
            (["application/json", "text/plain"], "text/plain"),
        ]
        for types, preferred_type in tests:
            with self.subTest(types, preferred_type=preferred_type):
                self.assertEqual(str(request.get_preferred_type(types)), preferred_type)
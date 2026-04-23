def test_params(self):
        tests = [
            ("text/plain", {}, {}),
            ("text/plain;q=0.7", {"q": "0.7"}, {}),
            ("text/plain;q=1.5", {"q": "1.5"}, {}),
            ("text/plain;q=xyz", {"q": "xyz"}, {}),
            ("text/plain;q=0.1234", {"q": "0.1234"}, {}),
            ("text/plain;version=2", {"version": "2"}, {"version": "2"}),
            (
                "text/plain;version=2;q=0.8",
                {"version": "2", "q": "0.8"},
                {"version": "2"},
            ),
            (
                "text/plain;q=0.8;version=2",
                {"q": "0.8", "version": "2"},
                {"version": "2"},
            ),
            (
                "text/plain; charset=UTF-8; q=0.3",
                {"charset": "UTF-8", "q": "0.3"},
                {"charset": "UTF-8"},
            ),
            (
                "text/plain ; q = 0.5 ; version = 3.0",
                {"q": "0.5", "version": "3.0"},
                {"version": "3.0"},
            ),
            ("text/plain; format=flowed", {"format": "flowed"}, {"format": "flowed"}),
            (
                "text/plain; format=flowed; q=0.4",
                {"format": "flowed", "q": "0.4"},
                {"format": "flowed"},
            ),
            ("text/*;q=0.2", {"q": "0.2"}, {}),
            ("*/json;q=0.9", {"q": "0.9"}, {}),
            ("application/json;q=0.9999", {"q": "0.9999"}, {}),
            ("text/html;q=0.0001", {"q": "0.0001"}, {}),
            ("text/html;q=0", {"q": "0"}, {}),
            ("text/html;q=0.", {"q": "0."}, {}),
            ("text/html;q=.8", {"q": ".8"}, {}),
            ("text/html;q= 0.9", {"q": "0.9"}, {}),
            ('text/html ; q = "0.6"', {"q": "0.6"}, {}),
        ]
        for accepted_type, params, range_params in tests:
            media_type = MediaType(accepted_type)
            with self.subTest(accepted_type, attr="params"):
                self.assertEqual(media_type.params, params)
            with self.subTest(accepted_type, attr="range_params"):
                self.assertEqual(media_type.range_params, range_params)
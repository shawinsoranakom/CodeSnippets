def test_header_max_length(self):
        base_header = "Content-Type: application/x-stuff; title*="
        base_header_len = len(base_header)

        test_data = [
            (MAX_HEADER_LENGTH, {}),
            (MAX_HEADER_LENGTH, {"max_length": None}),
            (MAX_HEADER_LENGTH + 1, {"max_length": None}),
            (100, {"max_length": 100}),
        ]
        for line_length, kwargs in test_data:
            with self.subTest(line_length=line_length, kwargs=kwargs):
                title = "x" * (line_length - base_header_len)
                line = base_header + title
                assert len(line) == line_length

                parsed = parse_header_parameters(line, **kwargs)

                expected = ("content-type: application/x-stuff", {"title": title})
                self.assertEqual(parsed, expected)
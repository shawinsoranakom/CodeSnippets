def test_header_too_long(self):
        test_data = [
            ("x" * (MAX_HEADER_LENGTH + 1), {}),
            ("x" * 101, {"max_length": 100}),
        ]
        for line, kwargs in test_data:
            with self.subTest(line_length=len(line), kwargs=kwargs):
                with self.assertRaises(ValueError):
                    parse_header_parameters(line, **kwargs)
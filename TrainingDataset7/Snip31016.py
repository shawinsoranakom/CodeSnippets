def test_quality(self):
        tests = [
            ("*/*; q=0.8", 0.8),
            ("*/*; q=0.0001", 0),
            ("*/*; q=0.12345", 0.123),
            ("*/*; q=0.1", 0.1),
            ("*/*; q=-1", 1),
            ("*/*; q=2", 1),
            ("*/*; q=h", 1),
            ("*/*; q=inf", 1),
            ("*/*; q=0", 0),
            ("*/*", 1),
        ]
        for accepted_type, quality in tests:
            with self.subTest(accepted_type, quality=quality):
                self.assertEqual(MediaType(accepted_type).quality, quality)
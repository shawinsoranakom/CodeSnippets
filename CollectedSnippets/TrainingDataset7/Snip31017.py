def test_specificity(self):
        tests = [
            ("*/*", 0),
            ("*/*;q=0.5", 0),
            ("text/*", 1),
            ("text/*;q=0.5", 1),
            ("text/html", 2),
            ("text/html;q=1", 2),
            ("text/html;q=0.5", 2),
            ("text/html;version=5", 3),
        ]
        for accepted_type, specificity in tests:
            with self.subTest(accepted_type, specificity=specificity):
                self.assertEqual(MediaType(accepted_type).specificity, specificity)
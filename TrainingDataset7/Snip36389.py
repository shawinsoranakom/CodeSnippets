def test_strip_tags_suspicious_operation_large_open_tags(self):
        items = [
            ">" + "<a" * 501,
            "<a" * 50 + "a" * 950,
        ]
        for value in items:
            with self.subTest(value=value):
                with self.assertRaises(SuspiciousOperation):
                    strip_tags(value)
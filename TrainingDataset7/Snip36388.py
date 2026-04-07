def test_strip_tags_suspicious_operation_max_depth(self):
        value = "<" * 51 + "a>" * 51, "<a>"
        with self.assertRaises(SuspiciousOperation):
            strip_tags(value)
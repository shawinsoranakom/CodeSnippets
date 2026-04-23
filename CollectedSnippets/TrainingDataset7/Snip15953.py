def test_json_display_for_field(self):
        tests = [
            ({"a": {"b": "c"}}, '{"a": {"b": "c"}}'),
            (["a", "b"], '["a", "b"]'),
            ("a", '"a"'),
            ({"a": "你好 世界"}, '{"a": "你好 世界"}'),
            ({("a", "b"): "c"}, "{('a', 'b'): 'c'}"),  # Invalid JSON.
        ]
        for value, display_value in tests:
            with self.subTest(value=value):
                self.assertEqual(
                    display_for_field(value, models.JSONField(), self.empty_value),
                    display_value,
                )
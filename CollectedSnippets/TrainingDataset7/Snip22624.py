def test_converted_value(self):
        field = JSONField(required=False)
        tests = [
            '["a", "b", "c"]',
            '{"a": 1, "b": 2}',
            "1",
            "1.5",
            '"foo"',
            "true",
            "false",
            "null",
        ]
        for json_string in tests:
            with self.subTest(json_string=json_string):
                val = field.clean(json_string)
                self.assertEqual(field.clean(val), val)
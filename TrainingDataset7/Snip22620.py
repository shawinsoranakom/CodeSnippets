def test_prepare_value(self):
        field = JSONField()
        self.assertEqual(field.prepare_value({"a": "b"}), '{"a": "b"}')
        self.assertEqual(field.prepare_value(None), "null")
        self.assertEqual(field.prepare_value("foo"), '"foo"')
        self.assertEqual(field.prepare_value("你好，世界"), '"你好，世界"')
        self.assertEqual(field.prepare_value({"a": "😀🐱"}), '{"a": "😀🐱"}')
        self.assertEqual(
            field.prepare_value(["你好，世界", "jaźń"]),
            '["你好，世界", "jaźń"]',
        )
def test_valid(self):
        field = JSONField()
        value = field.clean('{"a": "b"}')
        self.assertEqual(value, {"a": "b"})
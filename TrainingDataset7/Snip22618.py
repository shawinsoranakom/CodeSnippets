def test_valid_empty(self):
        field = JSONField(required=False)
        self.assertIsNone(field.clean(""))
        self.assertIsNone(field.clean(None))
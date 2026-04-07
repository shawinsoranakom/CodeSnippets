def test_none_allowed_as_value(self):
        field = HStoreField()
        self.assertEqual(field.clean({"a": None}, None), {"a": None})
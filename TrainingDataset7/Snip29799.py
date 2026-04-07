def test_valid(self):
        field = forms.HStoreField()
        value = field.clean('{"a": "b"}')
        self.assertEqual(value, {"a": "b"})
def test_not_string_values(self):
        field = forms.HStoreField()
        value = field.clean('{"a": 1}')
        self.assertEqual(value, {"a": "1"})
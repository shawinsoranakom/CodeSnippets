def test_none_value(self):
        field = forms.HStoreField()
        value = field.clean('{"a": null}')
        self.assertEqual(value, {"a": None})
def test_empty(self):
        field = forms.HStoreField(required=False)
        value = field.clean("")
        self.assertEqual(value, {})
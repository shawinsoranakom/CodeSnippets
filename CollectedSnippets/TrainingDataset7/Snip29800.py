def test_invalid_json(self):
        field = forms.HStoreField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean('{"a": "b"')
        self.assertEqual(cm.exception.messages[0], "Could not load JSON data.")
        self.assertEqual(cm.exception.code, "invalid_json")
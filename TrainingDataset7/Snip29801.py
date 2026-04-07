def test_non_dict_json(self):
        field = forms.HStoreField()
        msg = "Input must be a JSON dictionary."
        with self.assertRaisesMessage(exceptions.ValidationError, msg) as cm:
            field.clean('["a", "b", 1]')
        self.assertEqual(cm.exception.code, "invalid_format")
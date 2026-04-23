def test_not_a_string(self):
        field = HStoreField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean({"a": 1}, None)
        self.assertEqual(cm.exception.code, "not_a_string")
        self.assertEqual(
            cm.exception.message % cm.exception.params,
            "The value of “a” is not a string or null.",
        )
def test_missing_keys(self):
        validator = KeysValidator(keys=["a", "b"])
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator({"a": "foo", "c": "baz"})
        self.assertEqual(cm.exception.messages[0], "Some keys were missing: b")
        self.assertEqual(cm.exception.code, "missing_keys")
def test_extra_keys(self):
        validator = KeysValidator(keys=["a", "b"], strict=True)
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator({"a": "foo", "b": "bar", "c": "baz"})
        self.assertEqual(cm.exception.messages[0], "Some unknown keys were provided: c")
        self.assertEqual(cm.exception.code, "extra_keys")
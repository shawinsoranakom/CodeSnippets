def test_custom_messages(self):
        messages = {
            "missing_keys": "Foobar",
        }
        validator = KeysValidator(keys=["a", "b"], strict=True, messages=messages)
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator({"a": "foo", "c": "baz"})
        self.assertEqual(cm.exception.messages[0], "Foobar")
        self.assertEqual(cm.exception.code, "missing_keys")
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator({"a": "foo", "b": "bar", "c": "baz"})
        self.assertEqual(cm.exception.messages[0], "Some unknown keys were provided: c")
        self.assertEqual(cm.exception.code, "extra_keys")
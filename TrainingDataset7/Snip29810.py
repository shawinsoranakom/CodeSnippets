def test_strict_valid(self):
        validator = KeysValidator(keys=["a", "b"], strict=True)
        validator({"a": "foo", "b": "bar"})
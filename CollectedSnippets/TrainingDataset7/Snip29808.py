def test_simple_valid(self):
        validator = KeysValidator(keys=["a", "b"])
        validator({"a": "foo", "b": "bar", "c": "baz"})
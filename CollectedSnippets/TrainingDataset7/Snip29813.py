def test_deconstruct(self):
        messages = {
            "missing_keys": "Foobar",
        }
        validator = KeysValidator(keys=["a", "b"], strict=True, messages=messages)
        path, args, kwargs = validator.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.validators.KeysValidator")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs, {"keys": ["a", "b"], "strict": True, "messages": messages}
        )
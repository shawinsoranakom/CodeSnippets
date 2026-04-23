def test_lookups_with_key_transform(self):
        tests = (
            ("value__baz__has_key", "c"),
            ("value__baz__has_keys", ["a", "c"]),
            ("value__baz__has_any_keys", ["a", "x"]),
            ("value__has_key", KeyTextTransform("foo", "value")),
        )
        for lookup, value in tests:
            with self.subTest(lookup=lookup):
                self.assertIs(
                    NullableJSONModel.objects.filter(
                        **{lookup: value},
                    ).exists(),
                    True,
                )
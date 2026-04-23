def test_lookups_special_chars(self):
        test_keys = [
            "CONTROL",
            "single'",
            "dollar$",
            "dot.dot",
            "with space",
            "back\\slash",
            "question?mark",
            "user@name",
            "emo🤡'ji",
            "com,ma",
            "curly{{{brace}}}s",
            "escape\uffff'seq'\uffffue\uffff'nce",
        ]
        json_value = {key: "some value" for key in test_keys}
        obj = NullableJSONModel.objects.create(value=json_value)
        obj.refresh_from_db()
        self.assertEqual(obj.value, json_value)

        for key in test_keys:
            lookups = {
                "has_key": Q(value__has_key=key),
                "has_keys": Q(value__has_keys=[key, "CONTROL"]),
                "has_any_keys": Q(value__has_any_keys=[key, "does_not_exist"]),
                "exact": Q(**{f"value__{key}": "some value"}),
            }
            for lookup, condition in lookups.items():
                results = NullableJSONModel.objects.filter(condition)
                with self.subTest(key=key, lookup=lookup):
                    self.assertSequenceEqual(results, [obj])
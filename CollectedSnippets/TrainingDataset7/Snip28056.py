def test_lookups_special_chars_double_quotes(self):
        test_keys = [
            'double"',
            "m\\i@x. m🤡'a,t{{{ch}}}e?d$\"'es\uffff'ca\uffff'pe",
        ]
        json_value = {key: "some value" for key in test_keys}
        obj = NullableJSONModel.objects.create(value=json_value)
        obj.refresh_from_db()
        self.assertEqual(obj.value, json_value)
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__has_keys=test_keys), [obj]
        )
        for key in test_keys:
            with self.subTest(key=key):
                results = NullableJSONModel.objects.filter(
                    Q(value__has_key=key),
                    Q(value__has_any_keys=[key, "does_not_exist"]),
                    Q(**{f"value__{key}": "some value"}),
                )
                self.assertSequenceEqual(results, [obj])
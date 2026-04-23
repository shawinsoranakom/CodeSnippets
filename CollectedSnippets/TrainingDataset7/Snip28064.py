def test_key_values(self):
        qs = NullableJSONModel.objects.filter(value__h=True)
        tests = [
            ("value__a", "b"),
            ("value__c", 14),
            ("value__d", ["e", {"f": "g"}]),
            ("value__h", True),
            ("value__i", False),
            ("value__j", None),
            ("value__k", {"l": "m"}),
            ("value__n", [None, True, False]),
            ("value__p", 4.2),
            ("value__r", {"s": True, "t": False}),
        ]
        for lookup, expected in tests:
            with self.subTest(lookup=lookup):
                self.assertEqual(qs.values_list(lookup, flat=True).get(), expected)
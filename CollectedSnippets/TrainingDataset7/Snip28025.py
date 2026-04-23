def test_has_key_deep(self):
        tests = [
            (Q(value__baz__has_key="a"), self.objs[7]),
            (
                Q(value__has_key=KeyTransform("a", KeyTransform("baz", "value"))),
                self.objs[7],
            ),
            (Q(value__has_key=F("value__baz__a")), self.objs[7]),
            (
                Q(value__has_key=KeyTransform("c", KeyTransform("baz", "value"))),
                self.objs[7],
            ),
            (Q(value__has_key=F("value__baz__c")), self.objs[7]),
            (Q(value__d__1__has_key="f"), self.objs[4]),
            (
                Q(
                    value__has_key=KeyTransform(
                        "f", KeyTransform("1", KeyTransform("d", "value"))
                    )
                ),
                self.objs[4],
            ),
            (Q(value__has_key=F("value__d__1__f")), self.objs[4]),
        ]
        for condition, expected in tests:
            with self.subTest(condition=condition):
                self.assertSequenceEqual(
                    NullableJSONModel.objects.filter(condition),
                    [expected],
                )
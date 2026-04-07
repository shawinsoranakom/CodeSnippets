def test_numeric_lookups_with_expression(self):
        obj_greater = NullableJSONModel.objects.create(
            value={"target": 5, "comparison": 2}
        )
        obj_lesser = NullableJSONModel.objects.create(
            value={"target": 2, "comparison": 5}
        )
        obj_equal = NullableJSONModel.objects.create(
            value={"target": 2, "comparison": 2}
        )
        objs = [obj_greater.pk, obj_lesser.pk, obj_equal.pk]

        tests = [
            ("gt", [obj_greater]),
            ("lt", [obj_lesser]),
            ("gte", [obj_greater, obj_equal]),
            ("lte", [obj_lesser, obj_equal]),
        ]

        for lookup, expected in tests:
            with self.subTest(lookup=lookup):
                self.assertCountEqual(
                    NullableJSONModel.objects.filter(
                        id__in=objs,
                        **{f"value__target__{lookup}": F("value__comparison")},
                    ),
                    expected,
                )
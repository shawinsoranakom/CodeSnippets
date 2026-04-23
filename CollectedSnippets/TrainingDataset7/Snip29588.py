def test_lookups_autofield_array(self):
        qs = (
            NullableIntegerArrayModel.objects.filter(
                field__0__isnull=False,
            )
            .values("field__0")
            .annotate(
                arrayagg=ArrayAgg("id"),
            )
            .order_by("field__0")
        )
        tests = (
            ("contained_by", [self.objs[1].pk, self.objs[2].pk, 0], [2]),
            ("contains", [self.objs[2].pk], [2]),
            ("exact", [self.objs[3].pk], [20]),
            ("overlap", [self.objs[1].pk, self.objs[3].pk], [2, 20]),
        )
        for lookup, value, expected in tests:
            with self.subTest(lookup=lookup):
                self.assertSequenceEqual(
                    qs.filter(
                        **{"arrayagg__" + lookup: value},
                    ).values_list("field__0", flat=True),
                    expected,
                )
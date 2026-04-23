def test_decimal_contains_range(self):
        decimals = RangesModel.objects.bulk_create(
            [
                RangesModel(decimals=NumericRange(None, 10)),
                RangesModel(decimals=NumericRange(10, None)),
                RangesModel(decimals=NumericRange(5, 15)),
                RangesModel(decimals=NumericRange(5, 15, "(]")),
            ]
        )
        for contains, objs in [
            (199, [decimals[1]]),
            (1, [decimals[0]]),
            (15, [decimals[1], decimals[3]]),
        ]:
            with self.subTest(decimal_contains=contains):
                self.assertSequenceEqual(
                    RangesModel.objects.filter(decimals__contains=contains), objs
                )
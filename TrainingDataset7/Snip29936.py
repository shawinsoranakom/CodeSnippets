def test_bound_type(self):
        decimals = RangesModel.objects.bulk_create(
            [
                RangesModel(decimals=NumericRange(None, 10)),
                RangesModel(decimals=NumericRange(10, None)),
                RangesModel(decimals=NumericRange(5, 15)),
                RangesModel(decimals=NumericRange(5, 15, "(]")),
            ]
        )
        tests = [
            ("lower_inc", True, [decimals[1], decimals[2]]),
            ("lower_inc", False, [decimals[0], decimals[3]]),
            ("lower_inf", True, [decimals[0]]),
            ("lower_inf", False, [decimals[1], decimals[2], decimals[3]]),
            ("upper_inc", True, [decimals[3]]),
            ("upper_inc", False, [decimals[0], decimals[1], decimals[2]]),
            ("upper_inf", True, [decimals[1]]),
            ("upper_inf", False, [decimals[0], decimals[2], decimals[3]]),
        ]
        for lookup, filter_arg, excepted_result in tests:
            with self.subTest(lookup=lookup, filter_arg=filter_arg):
                self.assertSequenceEqual(
                    RangesModel.objects.filter(**{"decimals__%s" % lookup: filter_arg}),
                    excepted_result,
                )
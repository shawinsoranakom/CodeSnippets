def setUpTestData(cls):
        cls.objs = RangesModel.objects.bulk_create(
            [
                RangesModel(ints=NumericRange(0, 10)),
                RangesModel(ints=NumericRange(5, 15)),
                RangesModel(ints=NumericRange(None, 0)),
                RangesModel(ints=NumericRange(empty=True)),
                RangesModel(ints=None),
            ]
        )
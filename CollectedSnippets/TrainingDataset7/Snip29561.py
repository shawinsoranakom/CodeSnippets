def setUpTestData(cls):
        cls.objs = NullableIntegerArrayModel.objects.bulk_create(
            [
                NullableIntegerArrayModel(order=1, field=[1]),
                NullableIntegerArrayModel(order=2, field=[2]),
                NullableIntegerArrayModel(order=3, field=[2, 3]),
                NullableIntegerArrayModel(order=4, field=[20, 30, 40]),
                NullableIntegerArrayModel(order=5, field=None),
            ]
        )
def test_order_by_index(self):
        more_objs = (
            NullableIntegerArrayModel.objects.create(field=[1, 637]),
            NullableIntegerArrayModel.objects.create(field=[2, 1]),
            NullableIntegerArrayModel.objects.create(field=[3, -98123]),
            NullableIntegerArrayModel.objects.create(field=[4, 2]),
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.order_by("field__1"),
            [
                more_objs[2],
                more_objs[1],
                more_objs[3],
                self.objs[2],
                self.objs[3],
                more_objs[0],
                self.objs[4],
                self.objs[1],
                self.objs[0],
            ],
        )
def test_istartswith(self):
        self.assertSequenceEqualWithoutHyphens(
            NullableUUIDModel.objects.filter(field__istartswith="550E8400E29B4"),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(field__istartswith="550E8400-E29B-4"),
            [self.objs[1]],
        )
def test_endswith(self):
        self.assertSequenceEqualWithoutHyphens(
            NullableUUIDModel.objects.filter(field__endswith="a716446655440000"),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(field__endswith="a716-446655440000"),
            [self.objs[1]],
        )
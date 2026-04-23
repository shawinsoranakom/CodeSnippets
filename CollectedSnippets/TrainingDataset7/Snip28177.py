def test_startswith(self):
        self.assertSequenceEqualWithoutHyphens(
            NullableUUIDModel.objects.filter(field__startswith="550e8400e29b4"),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(field__startswith="550e8400-e29b-4"),
            [self.objs[1]],
        )
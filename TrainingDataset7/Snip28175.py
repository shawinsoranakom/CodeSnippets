def test_contains(self):
        self.assertSequenceEqualWithoutHyphens(
            NullableUUIDModel.objects.filter(field__contains="8400e29b"),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(field__contains="8400-e29b"),
            [self.objs[1]],
        )
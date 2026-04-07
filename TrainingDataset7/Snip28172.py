def test_exact(self):
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(
                field__exact="550e8400e29b41d4a716446655440000"
            ),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(
                field__exact="550e8400-e29b-41d4-a716-446655440000"
            ),
            [self.objs[1]],
        )
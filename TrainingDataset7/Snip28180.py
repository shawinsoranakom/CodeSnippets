def test_iendswith(self):
        self.assertSequenceEqualWithoutHyphens(
            NullableUUIDModel.objects.filter(field__iendswith="A716446655440000"),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(field__iendswith="A716-446655440000"),
            [self.objs[1]],
        )
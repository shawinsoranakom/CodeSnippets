def test_isnull(self):
        self.assertSequenceEqual(
            NullableUUIDModel.objects.filter(field__isnull=True), [self.objs[2]]
        )
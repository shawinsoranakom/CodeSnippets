def test_exclude_nullable_fields(self):
        number = Number.objects.create(num=1, other_num=1)
        Number.objects.create(num=2, other_num=2, another_num=2)
        self.assertSequenceEqual(
            Number.objects.exclude(other_num=F("another_num")),
            [number],
        )
        self.assertSequenceEqual(
            Number.objects.exclude(num=F("another_num")),
            [number],
        )
def test_ticket19672(self):
        self.assertSequenceEqual(
            Report.objects.filter(
                Q(creator__isnull=False) & ~Q(creator__extra__value=41)
            ),
            [self.r1],
        )
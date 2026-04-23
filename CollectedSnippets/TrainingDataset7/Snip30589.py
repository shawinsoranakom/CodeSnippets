def test_ticket2400(self):
        self.assertSequenceEqual(
            Author.objects.filter(item__isnull=True),
            [self.a3],
        )
        self.assertSequenceEqual(
            Tag.objects.filter(item__isnull=True),
            [self.t5],
        )
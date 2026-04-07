def test_ticket1801(self):
        self.assertSequenceEqual(
            Author.objects.filter(item=self.i2),
            [self.a2],
        )
        self.assertSequenceEqual(
            Author.objects.filter(item=self.i3),
            [self.a2],
        )
        self.assertSequenceEqual(
            Author.objects.filter(item=self.i2) & Author.objects.filter(item=self.i3),
            [self.a2],
        )
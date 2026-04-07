def test_ticket5261(self):
        # Test different empty excludes.
        self.assertSequenceEqual(
            Note.objects.exclude(Q()),
            [self.n1, self.n2],
        )
        self.assertSequenceEqual(
            Note.objects.filter(~Q()),
            [self.n1, self.n2],
        )
        self.assertSequenceEqual(
            Note.objects.filter(~Q() | ~Q()),
            [self.n1, self.n2],
        )
        self.assertSequenceEqual(
            Note.objects.exclude(~Q() & ~Q()),
            [self.n1, self.n2],
        )
        self.assertSequenceEqual(
            Note.objects.exclude(~Q() ^ ~Q()),
            [self.n1, self.n2],
        )
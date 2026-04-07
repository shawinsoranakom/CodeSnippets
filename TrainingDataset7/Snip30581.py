def test_ticket4510(self):
        self.assertSequenceEqual(
            Author.objects.filter(report__name="r1"),
            [self.a1],
        )
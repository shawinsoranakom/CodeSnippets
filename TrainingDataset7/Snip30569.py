def test_tickets_2080_3592(self):
        self.assertSequenceEqual(
            Author.objects.filter(item__name="one") | Author.objects.filter(name="a3"),
            [self.a1, self.a3],
        )
        self.assertSequenceEqual(
            Author.objects.filter(Q(item__name="one") | Q(name="a3")),
            [self.a1, self.a3],
        )
        self.assertSequenceEqual(
            Author.objects.filter(Q(name="a3") | Q(item__name="one")),
            [self.a1, self.a3],
        )
        self.assertSequenceEqual(
            Author.objects.filter(Q(item__name="three") | Q(report__name="r3")),
            [self.a2],
        )
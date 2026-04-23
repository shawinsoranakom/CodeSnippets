def test_tickets_4088_4306(self):
        self.assertSequenceEqual(Report.objects.filter(creator=1001), [self.r1])
        self.assertSequenceEqual(Report.objects.filter(creator__num=1001), [self.r1])
        self.assertSequenceEqual(Report.objects.filter(creator__id=1001), [])
        self.assertSequenceEqual(
            Report.objects.filter(creator__id=self.a1.id), [self.r1]
        )
        self.assertSequenceEqual(Report.objects.filter(creator__name="a1"), [self.r1])
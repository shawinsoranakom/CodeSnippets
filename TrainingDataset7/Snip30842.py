def test_ticket_21366(self):
        n = Note.objects.create(note="n", misc="m")
        e = ExtraInfo.objects.create(info="info", note=n)
        a = Author.objects.create(name="Author1", num=1, extra=e)
        Ranking.objects.create(rank=1, author=a)
        r1 = Report.objects.create(name="Foo", creator=a)
        r2 = Report.objects.create(name="Bar")
        Report.objects.create(name="Bar", creator=a)
        qs = Report.objects.filter(
            Q(creator__ranking__isnull=True) | Q(creator__ranking__rank=1, name="Foo")
        )
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 2)
        self.assertEqual(str(qs.query).count(" JOIN "), 2)
        self.assertSequenceEqual(qs.order_by("name"), [r2, r1])
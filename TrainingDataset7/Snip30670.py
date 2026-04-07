def setUpTestData(cls):
        # Ordering by 'rank' gives us rank2, rank1, rank3. Ordering by the
        # Meta.ordering will be rank3, rank2, rank1.
        cls.n1 = Note.objects.create(note="n1", misc="foo", id=1)
        cls.n2 = Note.objects.create(note="n2", misc="bar", id=2)
        e1 = ExtraInfo.objects.create(info="e1", note=cls.n1)
        e2 = ExtraInfo.objects.create(info="e2", note=cls.n2)
        a1 = Author.objects.create(name="a1", num=1001, extra=e1)
        a2 = Author.objects.create(name="a2", num=2002, extra=e1)
        a3 = Author.objects.create(name="a3", num=3003, extra=e2)
        cls.rank2 = Ranking.objects.create(rank=2, author=a2)
        cls.rank1 = Ranking.objects.create(rank=1, author=a3)
        cls.rank3 = Ranking.objects.create(rank=3, author=a1)
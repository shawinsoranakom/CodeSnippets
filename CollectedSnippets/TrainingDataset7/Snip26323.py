def test_reverse_selects(self):
        # Reverse m2m queries are supported (i.e., starting at the table that
        # doesn't have a ManyToManyField).
        python_journal = [self.p1]
        self.assertSequenceEqual(
            Publication.objects.filter(id__exact=self.p1.id), python_journal
        )
        self.assertSequenceEqual(
            Publication.objects.filter(pk=self.p1.id), python_journal
        )
        self.assertSequenceEqual(
            Publication.objects.filter(article__headline__startswith="NASA"),
            [self.p4, self.p2, self.p2, self.p3, self.p1],
        )

        self.assertSequenceEqual(
            Publication.objects.filter(article__id__exact=self.a1.id), python_journal
        )
        self.assertSequenceEqual(
            Publication.objects.filter(article__pk=self.a1.id), python_journal
        )
        self.assertSequenceEqual(
            Publication.objects.filter(article=self.a1.id), python_journal
        )
        self.assertSequenceEqual(
            Publication.objects.filter(article=self.a1), python_journal
        )

        self.assertSequenceEqual(
            Publication.objects.filter(article__in=[self.a1.id, self.a2.id]).distinct(),
            [self.p4, self.p2, self.p3, self.p1],
        )
        self.assertSequenceEqual(
            Publication.objects.filter(article__in=[self.a1.id, self.a2]).distinct(),
            [self.p4, self.p2, self.p3, self.p1],
        )
        self.assertSequenceEqual(
            Publication.objects.filter(article__in=[self.a1, self.a2]).distinct(),
            [self.p4, self.p2, self.p3, self.p1],
        )
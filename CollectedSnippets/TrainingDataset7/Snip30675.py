def test_ticket9848(self):
        # Make sure that updates which only filter on sub-tables don't
        # inadvertently update the wrong records (bug #9848).
        author_start = Author.objects.get(name="a1")
        ranking_start = Ranking.objects.get(author__name="a1")

        # Make sure that the IDs from different tables don't happen to match.
        self.assertSequenceEqual(
            Ranking.objects.filter(author__name="a1"),
            [self.rank3],
        )
        self.assertEqual(Ranking.objects.filter(author__name="a1").update(rank=4636), 1)

        r = Ranking.objects.get(author__name="a1")
        self.assertEqual(r.id, ranking_start.id)
        self.assertEqual(r.author.id, author_start.id)
        self.assertEqual(r.rank, 4636)
        r.rank = 3
        r.save()
        self.assertSequenceEqual(
            Ranking.objects.all(),
            [self.rank3, self.rank2, self.rank1],
        )
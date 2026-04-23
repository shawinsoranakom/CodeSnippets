def test_queryset_or_different_cached_items(self):
        tournament = self.t1
        organiser = self.o1
        with self.assertNumQueries(1):
            pools = tournament.pool_set.all() | organiser.pool_set.all()
            first = pools.filter(pk=self.p1.pk)[0]
            self.assertIs(first.tournament, tournament)
            self.assertIs(first.organiser, organiser)
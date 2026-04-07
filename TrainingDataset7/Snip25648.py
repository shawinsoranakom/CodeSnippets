def test_queryset_or_only_one_with_precache(self):
        tournament_1 = self.t1
        tournament_2 = self.t2
        # 2 queries here as pool 3 has tournament 2, which is not cached
        with self.assertNumQueries(2):
            pools = tournament_1.pool_set.all() | Pool.objects.filter(pk=self.p3.pk)
            related_objects = {pool.tournament for pool in pools}
            self.assertEqual(related_objects, {tournament_1, tournament_2})
        # and the other direction
        with self.assertNumQueries(2):
            pools = Pool.objects.filter(pk=self.p3.pk) | tournament_1.pool_set.all()
            related_objects = {pool.tournament for pool in pools}
            self.assertEqual(related_objects, {tournament_1, tournament_2})
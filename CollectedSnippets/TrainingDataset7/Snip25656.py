def test_reverse_one_to_one_select_related(self):
        with self.assertNumQueries(1):
            pool = Pool.objects.select_related("poolstyle").get(pk=self.p2.pk)
            style = pool.poolstyle
            self.assertIs(pool, style.pool)
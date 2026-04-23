def test_reverse_one_to_one_multi_select_related(self):
        with self.assertNumQueries(1):
            pools = list(Pool.objects.select_related("poolstyle").order_by("pk"))
            self.assertIs(pools[1], pools[1].poolstyle.pool)
            self.assertIs(pools[2], pools[2].poolstyle.pool)
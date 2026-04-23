def test_one_to_one_multi_select_related(self):
        with self.assertNumQueries(1):
            poolstyles = list(PoolStyle.objects.select_related("pool").order_by("pk"))
            self.assertIs(poolstyles[0], poolstyles[0].pool.poolstyle)
            self.assertIs(poolstyles[1], poolstyles[1].pool.poolstyle)
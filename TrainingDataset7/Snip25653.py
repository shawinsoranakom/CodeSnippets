def test_one_to_one_prefetch_related(self):
        with self.assertNumQueries(2):
            style = PoolStyle.objects.prefetch_related("pool").get(pk=self.ps1.pk)
            pool = style.pool
            self.assertIs(style, pool.poolstyle)
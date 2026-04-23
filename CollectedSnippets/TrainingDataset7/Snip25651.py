def test_one_to_one_select_related(self):
        with self.assertNumQueries(1):
            style = PoolStyle.objects.select_related("pool").get(pk=self.ps1.pk)
            pool = style.pool
            self.assertIs(style, pool.poolstyle)
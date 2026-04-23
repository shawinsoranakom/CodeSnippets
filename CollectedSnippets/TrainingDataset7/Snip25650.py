def test_one_to_one(self):
        with self.assertNumQueries(2):
            style = PoolStyle.objects.get(pk=self.ps1.pk)
            pool = style.pool
            self.assertIs(style, pool.poolstyle)
def test_clear_efficiency(self):
        r = Reporter.objects.create()
        for _ in range(3):
            r.article_set.create()
        with self.assertNumQueries(1):
            r.article_set.clear()
        self.assertEqual(r.article_set.count(), 0)
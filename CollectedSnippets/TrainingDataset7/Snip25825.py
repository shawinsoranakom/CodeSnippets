def test_in_ignore_none(self):
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(
                Article.objects.filter(id__in=[None, self.a1.id]),
                [self.a1],
            )
        sql = ctx.captured_queries[0]["sql"]
        self.assertIn("IN (%s)" % self.a1.pk, sql)
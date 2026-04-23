def test_in_ignore_none_with_unhashable_items(self):
        class UnhashableInt(int):
            __hash__ = None

        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(
                Article.objects.filter(id__in=[None, UnhashableInt(self.a1.id)]),
                [self.a1],
            )
        sql = ctx.captured_queries[0]["sql"]
        self.assertIn("IN (%s)" % self.a1.pk, sql)
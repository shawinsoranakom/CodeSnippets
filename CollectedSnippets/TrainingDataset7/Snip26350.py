def test_count_join_optimization(self):
        with self.assertNumQueries(1) as ctx:
            self.article.publications.count()
        self.assertNotIn("JOIN", ctx.captured_queries[0]["sql"])

        with self.assertNumQueries(1) as ctx:
            self.article.publications.count()
        self.assertNotIn("JOIN", ctx.captured_queries[0]["sql"])
        self.assertEqual(self.nullable_target_article.publications.count(), 0)
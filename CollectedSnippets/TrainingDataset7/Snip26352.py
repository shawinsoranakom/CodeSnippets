def test_exists_join_optimization(self):
        with self.assertNumQueries(1) as ctx:
            self.article.publications.exists()
        self.assertNotIn("JOIN", ctx.captured_queries[0]["sql"])

        self.article.publications.prefetch_related()
        with self.assertNumQueries(1) as ctx:
            self.article.publications.exists()
        self.assertNotIn("JOIN", ctx.captured_queries[0]["sql"])
        self.assertIs(self.nullable_target_article.publications.exists(), False)
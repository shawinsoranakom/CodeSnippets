def test_count_join_optimization_disabled(self):
        with (
            mock.patch.object(connection.features, "supports_foreign_keys", False),
            self.assertNumQueries(1) as ctx,
        ):
            self.article.publications.count()

        self.assertIn("JOIN", ctx.captured_queries[0]["sql"])
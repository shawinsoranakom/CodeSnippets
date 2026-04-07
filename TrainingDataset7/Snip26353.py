def test_exists_join_optimization_disabled(self):
        with (
            mock.patch.object(connection.features, "supports_foreign_keys", False),
            self.assertNumQueries(1) as ctx,
        ):
            self.article.publications.exists()

        self.assertIn("JOIN", ctx.captured_queries[0]["sql"])
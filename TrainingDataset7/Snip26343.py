def test_custom_default_manager_exists_count(self):
        a5 = Article.objects.create(headline="deleted")
        a5.publications.add(self.p2)
        with self.assertNumQueries(2) as ctx:
            self.assertEqual(
                self.p2.article_set.count(), self.p2.article_set.all().count()
            )
        self.assertIn("JOIN", ctx.captured_queries[0]["sql"])
        with self.assertNumQueries(2) as ctx:
            self.assertEqual(
                self.p3.article_set.exists(), self.p3.article_set.all().exists()
            )
        self.assertIn("JOIN", ctx.captured_queries[0]["sql"])
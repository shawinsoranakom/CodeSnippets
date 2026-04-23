def test_unnest_eligible_foreign_keys(self):
        reporter = Reporter.objects.create()
        with self.assertNumQueries(1) as ctx:
            articles = Article.objects.bulk_create(
                [
                    Article(pub_date=date.today(), reporter=reporter),
                    Article(pub_date=date.today(), reporter=reporter),
                ]
            )
        self.assertIn("UNNEST", ctx[0]["sql"])
        self.assertEqual(
            [article.reporter for article in articles], [reporter, reporter]
        )
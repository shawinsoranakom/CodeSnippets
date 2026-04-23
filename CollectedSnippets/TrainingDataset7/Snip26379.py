def test_create_relation_with_gettext_lazy(self):
        reporter = Reporter.objects.create(
            first_name="John", last_name="Smith", email="john.smith@example.com"
        )
        lazy = gettext_lazy("test")
        reporter.article_set.create(headline=lazy, pub_date=datetime.date(2011, 6, 10))
        notlazy = str(lazy)
        article = reporter.article_set.get()
        self.assertEqual(article.headline, notlazy)
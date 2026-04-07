def test_default_ordering_by_f_expression(self):
        """F expressions can be used in Meta.ordering."""
        articles = OrderedByFArticle.objects.all()
        articles.filter(headline="Article 2").update(author=self.author_2)
        articles.filter(headline="Article 3").update(author=self.author_1)
        self.assertQuerySetEqual(
            articles,
            ["Article 1", "Article 4", "Article 3", "Article 2"],
            attrgetter("headline"),
        )
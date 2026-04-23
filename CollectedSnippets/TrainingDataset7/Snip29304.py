def test_stages(self):
        # You can shorten this syntax with code like the following,  which is
        # especially useful if building the query in stages:
        articles = Article.objects.all()
        self.assertQuerySetEqual(
            articles.filter(headline__startswith="Hello")
            & articles.filter(headline__startswith="Goodbye"),
            [],
        )
        self.assertQuerySetEqual(
            articles.filter(headline__startswith="Hello")
            & articles.filter(headline__contains="bye"),
            ["Hello and goodbye"],
            attrgetter("headline"),
        )
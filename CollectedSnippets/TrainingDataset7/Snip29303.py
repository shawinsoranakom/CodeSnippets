def test_filter_or(self):
        self.assertQuerySetEqual(
            (
                Article.objects.filter(headline__startswith="Hello")
                | Article.objects.filter(headline__startswith="Goodbye")
            ),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(headline__contains="Hello")
            | Article.objects.filter(headline__contains="bye"),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(headline__iexact="Hello")
            | Article.objects.filter(headline__contains="ood"),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(
                Q(headline__startswith="Hello") | Q(headline__startswith="Goodbye")
            ),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )
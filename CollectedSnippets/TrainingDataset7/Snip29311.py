def test_q_and(self):
        # Q arg objects are ANDed
        self.assertQuerySetEqual(
            Article.objects.filter(
                Q(headline__startswith="Hello"), Q(headline__contains="bye")
            ),
            ["Hello and goodbye"],
            attrgetter("headline"),
        )
        # Q arg AND order is irrelevant
        self.assertQuerySetEqual(
            Article.objects.filter(
                Q(headline__contains="bye"), headline__startswith="Hello"
            ),
            ["Hello and goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(
                Q(headline__startswith="Hello") & Q(headline__startswith="Goodbye")
            ),
            [],
        )
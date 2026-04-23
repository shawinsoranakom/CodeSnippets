def test_q_exclude(self):
        self.assertQuerySetEqual(
            Article.objects.exclude(Q(headline__startswith="Hello")),
            ["Goodbye"],
            attrgetter("headline"),
        )
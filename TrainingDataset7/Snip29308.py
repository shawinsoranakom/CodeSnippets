def test_q_negated(self):
        # Q objects can be negated
        self.assertQuerySetEqual(
            Article.objects.filter(Q(pk=self.a1) | ~Q(pk=self.a2)),
            ["Hello", "Hello and goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(~Q(pk=self.a1) & ~Q(pk=self.a2)),
            ["Hello and goodbye"],
            attrgetter("headline"),
        )
        # This allows for more complex queries than filter() and exclude()
        # alone would allow
        self.assertQuerySetEqual(
            Article.objects.filter(Q(pk=self.a1) & (~Q(pk=self.a2) | Q(pk=self.a3))),
            ["Hello"],
            attrgetter("headline"),
        )
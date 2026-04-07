def test_pk_q(self):
        self.assertQuerySetEqual(
            Article.objects.filter(Q(pk=self.a1) | Q(pk=self.a2)),
            ["Hello", "Goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(Q(pk=self.a1) | Q(pk=self.a2) | Q(pk=self.a3)),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )
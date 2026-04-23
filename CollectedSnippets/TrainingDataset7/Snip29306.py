def test_pk_in(self):
        self.assertQuerySetEqual(
            Article.objects.filter(pk__in=[self.a1, self.a2, self.a3]),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(pk__in=(self.a1, self.a2, self.a3)),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.filter(pk__in=[self.a1, self.a2, self.a3, 40000]),
            ["Hello", "Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )
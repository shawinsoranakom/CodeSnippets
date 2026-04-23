def test_complex_filter(self):
        # The 'complex_filter' method supports framework features such as
        # 'limit_choices_to' which normally take a single dictionary of lookup
        # arguments but need to support arbitrary queries via Q objects too.
        self.assertQuerySetEqual(
            Article.objects.complex_filter({"pk": self.a1}),
            ["Hello"],
            attrgetter("headline"),
        )

        self.assertQuerySetEqual(
            Article.objects.complex_filter(Q(pk=self.a1) | Q(pk=self.a2)),
            ["Hello", "Goodbye"],
            attrgetter("headline"),
        )
def test_simple_example(self):
        self.assertQuerySetEqual(
            Client.objects.annotate(
                discount=Case(
                    When(account_type=Client.GOLD, then=Value("5%")),
                    When(account_type=Client.PLATINUM, then=Value("10%")),
                    default=Value("0%"),
                ),
            ).order_by("pk"),
            [("Jane Doe", "0%"), ("James Smith", "5%"), ("Jack Black", "10%")],
            transform=attrgetter("name", "discount"),
        )
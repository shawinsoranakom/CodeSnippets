def test_lookup_example(self):
        a_month_ago = date.today() - timedelta(days=30)
        a_year_ago = date.today() - timedelta(days=365)
        self.assertQuerySetEqual(
            Client.objects.annotate(
                discount=Case(
                    When(registered_on__lte=a_year_ago, then=Value("10%")),
                    When(registered_on__lte=a_month_ago, then=Value("5%")),
                    default=Value("0%"),
                ),
            ).order_by("pk"),
            [("Jane Doe", "5%"), ("James Smith", "0%"), ("Jack Black", "10%")],
            transform=attrgetter("name", "discount"),
        )
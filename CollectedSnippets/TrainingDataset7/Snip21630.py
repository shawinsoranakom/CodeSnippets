def test_conditional_update_example(self):
        a_month_ago = date.today() - timedelta(days=30)
        a_year_ago = date.today() - timedelta(days=365)
        Client.objects.update(
            account_type=Case(
                When(registered_on__lte=a_year_ago, then=Value(Client.PLATINUM)),
                When(registered_on__lte=a_month_ago, then=Value(Client.GOLD)),
                default=Value(Client.REGULAR),
            ),
        )
        self.assertQuerySetEqual(
            Client.objects.order_by("pk"),
            [("Jane Doe", "G"), ("James Smith", "R"), ("Jack Black", "P")],
            transform=attrgetter("name", "account_type"),
        )
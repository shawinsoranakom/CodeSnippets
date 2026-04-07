def test_conditional_aggregation_example(self):
        Client.objects.create(
            name="Jean Grey",
            account_type=Client.REGULAR,
            registered_on=date.today(),
        )
        Client.objects.create(
            name="James Bond",
            account_type=Client.PLATINUM,
            registered_on=date.today(),
        )
        Client.objects.create(
            name="Jane Porter",
            account_type=Client.PLATINUM,
            registered_on=date.today(),
        )
        self.assertEqual(
            Client.objects.aggregate(
                regular=Count("pk", filter=Q(account_type=Client.REGULAR)),
                gold=Count("pk", filter=Q(account_type=Client.GOLD)),
                platinum=Count("pk", filter=Q(account_type=Client.PLATINUM)),
            ),
            {"regular": 2, "gold": 1, "platinum": 3},
        )
        # This was the example before the filter argument was added.
        self.assertEqual(
            Client.objects.aggregate(
                regular=Sum(
                    Case(
                        When(account_type=Client.REGULAR, then=1),
                    )
                ),
                gold=Sum(
                    Case(
                        When(account_type=Client.GOLD, then=1),
                    )
                ),
                platinum=Sum(
                    Case(
                        When(account_type=Client.PLATINUM, then=1),
                    )
                ),
            ),
            {"regular": 2, "gold": 1, "platinum": 3},
        )
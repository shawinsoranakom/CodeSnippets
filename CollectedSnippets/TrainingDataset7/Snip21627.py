def setUpTestData(cls):
        Client.objects.create(
            name="Jane Doe",
            account_type=Client.REGULAR,
            registered_on=date.today() - timedelta(days=36),
        )
        Client.objects.create(
            name="James Smith",
            account_type=Client.GOLD,
            registered_on=date.today() - timedelta(days=5),
        )
        Client.objects.create(
            name="Jack Black",
            account_type=Client.PLATINUM,
            registered_on=date.today() - timedelta(days=10 * 365),
        )
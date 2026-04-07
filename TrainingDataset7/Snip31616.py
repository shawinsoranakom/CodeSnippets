def test_regression_8036(self):
        """
        Regression test for bug #8036

        the first related model in the tests below
        ("state") is empty and we try to select the more remotely related
        state__country. The regression here was not skipping the empty column
        results for country before getting status.
        """

        Country.objects.create(name="Australia")
        active = ClientStatus.objects.create(name="active")
        client = Client.objects.create(name="client", status=active)

        self.assertEqual(client.status, active)
        self.assertEqual(Client.objects.select_related()[0].status, active)
        self.assertEqual(Client.objects.select_related("state")[0].status, active)
        self.assertEqual(
            Client.objects.select_related("state", "status")[0].status, active
        )
        self.assertEqual(
            Client.objects.select_related("state__country")[0].status, active
        )
        self.assertEqual(
            Client.objects.select_related("state__country", "status")[0].status, active
        )
        self.assertEqual(Client.objects.select_related("status")[0].status, active)
def test_regression_12851(self):
        """
        Regression for #12851

        Deferred fields are used correctly if you select_related a subset
        of fields.
        """
        australia = Country.objects.create(name="Australia")
        active = ClientStatus.objects.create(name="active")

        wa = State.objects.create(name="Western Australia", country=australia)
        Client.objects.create(name="Brian Burke", state=wa, status=active)
        burke = (
            Client.objects.select_related("state")
            .defer("state__name")
            .get(name="Brian Burke")
        )

        self.assertEqual(burke.name, "Brian Burke")
        self.assertEqual(burke.state.name, "Western Australia")

        # Still works if we're dealing with an inherited class
        SpecialClient.objects.create(
            name="Troy Buswell", state=wa, status=active, value=42
        )
        troy = (
            SpecialClient.objects.select_related("state")
            .defer("state__name")
            .get(name="Troy Buswell")
        )

        self.assertEqual(troy.name, "Troy Buswell")
        self.assertEqual(troy.value, 42)
        self.assertEqual(troy.state.name, "Western Australia")

        # Still works if we defer an attribute on the inherited class
        troy = (
            SpecialClient.objects.select_related("state")
            .defer("value", "state__name")
            .get(name="Troy Buswell")
        )

        self.assertEqual(troy.name, "Troy Buswell")
        self.assertEqual(troy.value, 42)
        self.assertEqual(troy.state.name, "Western Australia")

        # Also works if you use only, rather than defer
        troy = (
            SpecialClient.objects.select_related("state")
            .only("name", "state")
            .get(name="Troy Buswell")
        )

        self.assertEqual(troy.name, "Troy Buswell")
        self.assertEqual(troy.value, 42)
        self.assertEqual(troy.state.name, "Western Australia")
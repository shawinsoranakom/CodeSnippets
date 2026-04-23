def test_proxy_inheritance_supported(self):
        ProxyCountry.objects.bulk_create(
            [
                ProxyCountry(name="Qwghlm", iso_two_letter="QW"),
                Country(name="Tortall", iso_two_letter="TA"),
            ]
        )
        self.assertQuerySetEqual(
            ProxyCountry.objects.all(),
            {"Qwghlm", "Tortall"},
            attrgetter("name"),
            ordered=False,
        )

        ProxyProxyCountry.objects.bulk_create(
            [
                ProxyProxyCountry(name="Netherlands", iso_two_letter="NT"),
            ]
        )
        self.assertQuerySetEqual(
            ProxyProxyCountry.objects.all(),
            {
                "Qwghlm",
                "Tortall",
                "Netherlands",
            },
            attrgetter("name"),
            ordered=False,
        )
def test_simple(self):
        created = Country.objects.bulk_create(self.data)
        self.assertEqual(created, self.data)
        self.assertQuerySetEqual(
            Country.objects.order_by("-name"),
            [
                "United States of America",
                "The Netherlands",
                "Germany",
                "Czech Republic",
            ],
            attrgetter("name"),
        )

        created = Country.objects.bulk_create([])
        self.assertEqual(created, [])
        self.assertEqual(Country.objects.count(), 4)
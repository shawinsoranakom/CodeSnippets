def test_filter_inherited_on_null(self):
        # Refs #12567
        Supplier.objects.create(
            name="Central market",
            address="610 some street",
        )
        self.assertQuerySetEqual(
            Place.objects.filter(supplier__isnull=False),
            [
                "Central market",
            ],
            attrgetter("name"),
        )
        self.assertQuerySetEqual(
            Place.objects.filter(supplier__isnull=True).order_by("name"),
            [
                "Demon Dogs",
                "Ristorante Miron",
            ],
            attrgetter("name"),
        )
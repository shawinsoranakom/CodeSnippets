def test_exclude_inherited_on_null(self):
        # Refs #12567
        Supplier.objects.create(
            name="Central market",
            address="610 some street",
        )
        self.assertQuerySetEqual(
            Place.objects.exclude(supplier__isnull=False).order_by("name"),
            [
                "Demon Dogs",
                "Ristorante Miron",
            ],
            attrgetter("name"),
        )
        self.assertQuerySetEqual(
            Place.objects.exclude(supplier__isnull=True),
            [
                "Central market",
            ],
            attrgetter("name"),
        )
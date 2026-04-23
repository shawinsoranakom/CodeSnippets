def test_ticket_7302(self):
        # Reserved names are appropriately escaped
        r_a = ReservedName.objects.create(name="a", order=42)
        r_b = ReservedName.objects.create(name="b", order=37)
        self.assertSequenceEqual(
            ReservedName.objects.order_by("order"),
            [r_b, r_a],
        )
        self.assertSequenceEqual(
            ReservedName.objects.extra(
                select={"stuff": "name"}, order_by=("order", "stuff")
            ),
            [r_b, r_a],
        )
def test_recursive_m2m_set(self):
        # Set new relationships for Chuck.
        self.c.colleagues.set(
            [self.b, self.d],
            through_defaults={
                "first_meet": datetime.date(2013, 1, 5),
            },
        )
        self.assertSequenceEqual(self.c.colleagues.order_by("name"), [self.b, self.d])
        # Reverse m2m relationships is removed.
        self.assertSequenceEqual(self.a.colleagues.order_by("name"), [self.b, self.d])
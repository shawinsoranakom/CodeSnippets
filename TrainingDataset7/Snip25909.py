def test_recursive_m2m_reverse_add(self):
        # Add m2m for Anne in reverse direction.
        self.b.colleagues.add(
            self.a,
            through_defaults={
                "first_meet": datetime.date(2013, 1, 5),
            },
        )
        self.assertCountEqual(self.a.colleagues.all(), [self.b, self.c, self.d])
        self.assertSequenceEqual(self.b.colleagues.all(), [self.a])
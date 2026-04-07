def test_m2m_through_reverse_returns_valid_members(self):
        # We start out by making sure that Bob is in no groups.
        self.assertQuerySetEqual(self.bob.groups.all(), [])

        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.republican
        )

        # Bob should be in the CIA and a Republican
        self.assertQuerySetEqual(
            self.bob.groups.all(), ["CIA", "Republican"], attrgetter("name")
        )
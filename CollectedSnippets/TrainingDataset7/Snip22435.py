def test_m2m_through_forward_returns_valid_members(self):
        # We start out by making sure that the Group 'CIA' has no members.
        self.assertQuerySetEqual(self.cia.members.all(), [])

        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        Membership.objects.create(
            membership_country=self.usa, person=self.jim, group=self.cia
        )

        # Bob and Jim should be members of the CIA.

        self.assertQuerySetEqual(
            self.cia.members.all(), ["Bob", "Jim"], attrgetter("name")
        )
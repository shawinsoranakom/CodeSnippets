def test_m2m_through_reverse_ignores_invalid_members(self):
        # We start out by making sure that Jane has no groups.
        self.assertQuerySetEqual(self.jane.groups.all(), [])

        # Something adds jane to group CIA but Jane is in Soviet Union which
        # isn't CIA's country.
        Membership.objects.create(
            membership_country=self.usa, person=self.jane, group=self.cia
        )

        # Jane should still not be in any groups
        self.assertQuerySetEqual(self.jane.groups.all(), [])
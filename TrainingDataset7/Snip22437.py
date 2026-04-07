def test_m2m_through_forward_ignores_invalid_members(self):
        # We start out by making sure that the Group 'CIA' has no members.
        self.assertQuerySetEqual(self.cia.members.all(), [])

        # Something adds jane to group CIA but Jane is in Soviet Union which
        # isn't CIA's country.
        Membership.objects.create(
            membership_country=self.usa, person=self.jane, group=self.cia
        )

        # There should still be no members in CIA
        self.assertQuerySetEqual(self.cia.members.all(), [])
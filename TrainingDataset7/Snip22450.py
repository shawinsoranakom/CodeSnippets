def test_isnull_lookup(self):
        m1 = Membership.objects.create(
            person_id=self.bob.id,
            membership_country_id=self.usa.id,
            group_id=None,
        )
        m2 = Membership.objects.create(
            person_id=self.jim.id,
            membership_country_id=None,
            group_id=self.cia.id,
        )
        m3 = Membership.objects.create(
            person_id=self.jane.id,
            membership_country_id=None,
            group_id=None,
        )
        m4 = Membership.objects.create(
            person_id=self.george.id,
            membership_country_id=self.soviet_union.id,
            group_id=self.kgb.id,
        )
        for member in [m1, m2, m3]:
            with self.assertRaises(Membership.group.RelatedObjectDoesNotExist):
                getattr(member, "group")
        self.assertSequenceEqual(
            Membership.objects.filter(group__isnull=True),
            [m1, m2, m3],
        )
        self.assertSequenceEqual(
            Membership.objects.filter(group__isnull=False),
            [m4],
        )
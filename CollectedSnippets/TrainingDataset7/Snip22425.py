def test_query_filters_correctly(self):
        # Creating a to valid memberships
        Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.bob.id,
            group_id=self.cia.id,
        )
        Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.jim.id,
            group_id=self.cia.id,
        )

        # Creating an invalid membership
        Membership.objects.create(
            membership_country_id=self.soviet_union.id,
            person_id=self.george.id,
            group_id=self.cia.id,
        )

        self.assertQuerySetEqual(
            Membership.objects.filter(person__name__contains="o"),
            [self.bob.id],
            attrgetter("person_id"),
        )
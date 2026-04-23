def test_forward_in_lookup_filters_correctly(self):
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
            Membership.objects.filter(person__in=[self.george, self.jim]),
            [
                self.jim.id,
            ],
            attrgetter("person_id"),
        )
        self.assertQuerySetEqual(
            Membership.objects.filter(person__in=Person.objects.filter(name="Jim")),
            [
                self.jim.id,
            ],
            attrgetter("person_id"),
        )
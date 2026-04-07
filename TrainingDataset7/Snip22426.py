def test_reverse_query_filters_correctly(self):
        timemark = datetime.datetime.now(tz=datetime.UTC).replace(tzinfo=None)
        timedelta = datetime.timedelta(days=1)

        # Creating a to valid memberships
        Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.bob.id,
            group_id=self.cia.id,
            date_joined=timemark - timedelta,
        )
        Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.jim.id,
            group_id=self.cia.id,
            date_joined=timemark + timedelta,
        )

        # Creating an invalid membership
        Membership.objects.create(
            membership_country_id=self.soviet_union.id,
            person_id=self.george.id,
            group_id=self.cia.id,
            date_joined=timemark + timedelta,
        )

        self.assertQuerySetEqual(
            Person.objects.filter(membership__date_joined__gte=timemark),
            ["Jim"],
            attrgetter("name"),
        )
def test_reverse_query_returns_correct_result(self):
        # Creating a valid membership because it has the same country has the
        # person
        Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.bob.id,
            group_id=self.cia.id,
        )

        # Creating an invalid membership because it has a different country has
        # the person.
        Membership.objects.create(
            membership_country_id=self.soviet_union.id,
            person_id=self.bob.id,
            group_id=self.republican.id,
        )

        with self.assertNumQueries(1):
            membership = self.bob.membership_set.get()
            self.assertEqual(membership.group_id, self.cia.id)
            self.assertIs(membership.person, self.bob)
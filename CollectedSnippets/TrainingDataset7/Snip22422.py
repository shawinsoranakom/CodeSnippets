def test_get_succeeds_on_multicolumn_match(self):
        # Membership objects have access to their related Person if both
        # country_ids match between them
        membership = Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.bob.id,
            group_id=self.cia.id,
        )

        person = membership.person
        self.assertEqual((person.id, person.name), (self.bob.id, "Bob"))
def test_get_fails_on_multicolumn_mismatch(self):
        # Membership objects returns DoesNotExist error when there is no
        # Person with the same id and country_id
        membership = Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.jane.id,
            group_id=self.cia.id,
        )

        with self.assertRaises(Person.DoesNotExist):
            getattr(membership, "person")
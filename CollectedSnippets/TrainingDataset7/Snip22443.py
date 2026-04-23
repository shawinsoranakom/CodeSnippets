def test_refresh_foreign_object(self):
        member = Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        member.person = self.jim
        with self.assertNumQueries(1):
            member.refresh_from_db()
        self.assertEqual(member.person, self.bob)
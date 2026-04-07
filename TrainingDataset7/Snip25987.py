def test_query_second_model_by_intermediate_model_attribute(self):
        Membership.objects.create(
            person=self.jane, group=self.roll, invite_reason="She was just awesome."
        )
        Membership.objects.create(
            person=self.jim, group=self.roll, invite_reason="He is good."
        )
        Membership.objects.create(person=self.bob, group=self.roll)

        qs = Person.objects.filter(membership__invite_reason="She was just awesome.")
        self.assertQuerySetEqual(qs, ["Jane"], attrgetter("name"))
def test_query_model_by_intermediate_can_return_non_unique_queryset(self):
        Membership.objects.create(person=self.jim, group=self.rock)
        Membership.objects.create(
            person=self.jane, group=self.rock, date_joined=datetime(2006, 1, 1)
        )
        Membership.objects.create(
            person=self.bob, group=self.roll, date_joined=datetime(2004, 1, 1)
        )
        Membership.objects.create(person=self.jim, group=self.roll)
        Membership.objects.create(
            person=self.jane, group=self.roll, date_joined=datetime(2004, 1, 1)
        )

        qs = Person.objects.filter(membership__date_joined__gt=datetime(2004, 1, 1))
        self.assertQuerySetEqual(qs, ["Jane", "Jim", "Jim"], attrgetter("name"))
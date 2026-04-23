def test_query_model_by_related_model_name(self):
        Membership.objects.create(person=self.jim, group=self.rock)
        Membership.objects.create(person=self.jane, group=self.rock)
        Membership.objects.create(person=self.bob, group=self.roll)
        Membership.objects.create(person=self.jim, group=self.roll)
        Membership.objects.create(person=self.jane, group=self.roll)

        self.assertQuerySetEqual(
            Person.objects.filter(group__name="Rock"),
            ["Jane", "Jim"],
            attrgetter("name"),
        )
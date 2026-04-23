def test_query_model_by_custom_related_name(self):
        CustomMembership.objects.create(person=self.bob, group=self.rock)
        CustomMembership.objects.create(person=self.jim, group=self.rock)

        self.assertQuerySetEqual(
            Person.objects.filter(custom__name="Rock"),
            ["Bob", "Jim"],
            attrgetter("name"),
        )
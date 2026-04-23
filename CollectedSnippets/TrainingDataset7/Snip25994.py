def test_custom_related_name_reverse_non_empty_qs(self):
        CustomMembership.objects.create(person=self.bob, group=self.rock)
        CustomMembership.objects.create(person=self.jim, group=self.rock)

        self.assertQuerySetEqual(self.bob.custom.all(), ["Rock"], attrgetter("name"))
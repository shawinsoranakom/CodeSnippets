def test_retrieve_reverse_intermediate_items(self):
        Membership.objects.create(person=self.jim, group=self.rock)
        Membership.objects.create(person=self.jim, group=self.roll)

        expected = ["Rock", "Roll"]
        self.assertQuerySetEqual(self.jim.group_set.all(), expected, attrgetter("name"))
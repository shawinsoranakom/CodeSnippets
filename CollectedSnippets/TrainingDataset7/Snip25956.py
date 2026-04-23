def test_retrieve_intermediate_items(self):
        Membership.objects.create(person=self.jim, group=self.rock)
        Membership.objects.create(person=self.jane, group=self.rock)

        expected = ["Jane", "Jim"]
        self.assertQuerySetEqual(self.rock.members.all(), expected, attrgetter("name"))
def test_set_on_reverse_m2m_with_intermediate_model(self):
        members = list(Group.objects.filter(name__in=["Rock", "Roll"]))
        self.bob.group_set.set(members)
        self.assertSequenceEqual(self.bob.group_set.all(), [self.rock, self.roll])
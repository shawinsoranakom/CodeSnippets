def test_custom_related_name_doesnt_conflict_with_fky_related_name(self):
        c = CustomMembership.objects.create(person=self.bob, group=self.rock)
        self.assertSequenceEqual(self.bob.custom_person_related_name.all(), [c])
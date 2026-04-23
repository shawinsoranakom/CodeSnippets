def test_clear_on_reverse_removes_all_the_m2m_relationships(self):
        Membership.objects.create(person=self.jim, group=self.rock)
        Membership.objects.create(person=self.jim, group=self.roll)

        self.jim.group_set.clear()

        self.assertQuerySetEqual(self.jim.group_set.all(), [])
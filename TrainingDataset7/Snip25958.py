def test_filter_on_intermediate_model(self):
        m1 = Membership.objects.create(person=self.jim, group=self.rock)
        m2 = Membership.objects.create(person=self.jane, group=self.rock)

        queryset = Membership.objects.filter(group=self.rock)

        self.assertSequenceEqual(queryset, [m1, m2])
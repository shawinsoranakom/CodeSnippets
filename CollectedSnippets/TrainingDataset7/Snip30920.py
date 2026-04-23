def test_filter_reverse_fk(self):
        self.assert_pickles(Group.objects.filter(event=1))
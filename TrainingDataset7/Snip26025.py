def test_retrieve_reverse_m2m_items(self):
        self.assertCountEqual(self.bob.group_set.all(), [self.rock, self.roll])
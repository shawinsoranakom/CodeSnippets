def test_retrieve_reverse_m2m_items_via_custom_id_intermediary(self):
        self.assertCountEqual(self.frank.group_set.all(), [self.rock, self.roll])
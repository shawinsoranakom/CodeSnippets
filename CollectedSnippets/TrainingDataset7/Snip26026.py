def test_retrieve_forward_m2m_items(self):
        self.assertSequenceEqual(self.roll.members.all(), [self.bob])
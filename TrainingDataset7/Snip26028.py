def test_retrieve_forward_m2m_items_via_custom_id_intermediary(self):
        self.assertSequenceEqual(self.roll.user_members.all(), [self.frank])
def test_recursive_m2m_clear(self):
        # Clear m2m for Anne.
        self.a.colleagues.clear()
        self.assertSequenceEqual(self.a.friends.all(), [])
        # Reverse m2m relationships is removed.
        self.assertSequenceEqual(self.c.colleagues.all(), [self.d])
        self.assertSequenceEqual(self.d.colleagues.all(), [self.c])
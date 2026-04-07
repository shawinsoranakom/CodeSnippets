def test_recursive_m2m_clear(self):
        # Clear m2m for Anne.
        self.a.friends.clear()
        self.assertSequenceEqual(self.a.friends.all(), [])
        # Reverse m2m relationships should be removed.
        self.assertSequenceEqual(self.c.friends.all(), [self.d])
        self.assertSequenceEqual(self.d.friends.all(), [self.c])
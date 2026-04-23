def test_recursive_m2m_reverse_add(self):
        # Add m2m for Anne in reverse direction.
        self.b.friends.add(self.a)
        self.assertSequenceEqual(self.a.friends.all(), [self.b, self.c, self.d])
        self.assertSequenceEqual(self.b.friends.all(), [self.a])
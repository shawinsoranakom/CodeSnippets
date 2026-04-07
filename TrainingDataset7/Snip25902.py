def test_recursive_m2m_remove(self):
        self.b.friends.remove(self.a)
        self.assertSequenceEqual(self.a.friends.all(), [self.c, self.d])
        self.assertSequenceEqual(self.b.friends.all(), [])
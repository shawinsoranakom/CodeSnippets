def test_recursive_m2m_remove(self):
        self.b.colleagues.remove(self.a)
        self.assertSequenceEqual(self.a.colleagues.all(), [self.c, self.d])
        self.assertSequenceEqual(self.b.colleagues.all(), [])
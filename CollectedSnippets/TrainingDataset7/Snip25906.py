def test_recursive_m2m_related_to_self(self):
        self.a.idols.add(self.a)
        self.assertSequenceEqual(self.a.idols.all(), [self.a])
        self.assertSequenceEqual(self.a.stalkers.all(), [self.a])
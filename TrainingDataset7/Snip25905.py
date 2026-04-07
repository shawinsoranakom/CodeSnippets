def test_recursive_m2m_add_in_both_directions(self):
        # Adding the same relation twice results in a single relation.
        self.a.idols.add(self.d)
        self.d.stalkers.add(self.a)
        self.assertSequenceEqual(self.a.idols.all(), [self.d])
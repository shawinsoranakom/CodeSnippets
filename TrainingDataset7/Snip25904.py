def test_recursive_m2m_add_via_related_name(self):
        # Add m2m with custom related name for Anne in reverse direction.
        self.d.stalkers.add(self.a)
        self.assertSequenceEqual(self.a.idols.all(), [self.d])
        self.assertSequenceEqual(self.a.stalkers.all(), [])
def test_create_on_reverse_m2m_with_intermediate_model(self):
        funk = self.bob.group_set.create(name="Funk")
        self.assertSequenceEqual(self.bob.group_set.all(), [funk])
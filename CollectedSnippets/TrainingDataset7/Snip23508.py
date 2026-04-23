def test_generic_relations_m2m_mimic(self):
        """
        Objects with declared GenericRelations can be tagged directly -- the
        API mimics the many-to-many API.
        """
        self.assertSequenceEqual(self.lion.tags.all(), [self.hairy, self.yellow])
        self.assertSequenceEqual(self.bacon.tags.all(), [self.fatty, self.salty])
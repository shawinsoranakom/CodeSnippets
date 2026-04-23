def test_known_related_objects_identity_preservation(self):
        """Known related objects identity is preserved."""
        self.assertIs(self.herbie.car, self.car)
        self.assertIs(self.herbie.belongs_to, self.jim_douglas)
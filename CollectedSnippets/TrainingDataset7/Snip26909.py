def test_deconstructible_dict(self):
        """Nested deconstruction descends into dict values."""
        # When dicts contain items whose values deconstruct to identical
        # values, those dicts should be considered equal for the purpose of
        # detecting state changes (even if the original values are unequal).
        changes = self.get_changes(
            [self.author_name_deconstructible_dict_1],
            [self.author_name_deconstructible_dict_2],
        )
        self.assertEqual(changes, {})
        # Legitimate differences within the deconstructed dicts should be
        # reported as a change
        changes = self.get_changes(
            [self.author_name_deconstructible_dict_1],
            [self.author_name_deconstructible_dict_3],
        )
        self.assertEqual(len(changes), 1)
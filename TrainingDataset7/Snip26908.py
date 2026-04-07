def test_deconstructible_tuple(self):
        """Nested deconstruction descends into tuples."""
        # When tuples contain items that deconstruct to identical values, those
        # tuples should be considered equal for the purpose of detecting state
        # changes (even if the original items are unequal).
        changes = self.get_changes(
            [self.author_name_deconstructible_tuple_1],
            [self.author_name_deconstructible_tuple_2],
        )
        self.assertEqual(changes, {})
        # Legitimate differences within the deconstructed tuples should be
        # reported as a change
        changes = self.get_changes(
            [self.author_name_deconstructible_tuple_1],
            [self.author_name_deconstructible_tuple_3],
        )
        self.assertEqual(len(changes), 1)
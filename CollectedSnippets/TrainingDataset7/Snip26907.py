def test_deconstructible_list(self):
        """Nested deconstruction descends into lists."""
        # When lists contain items that deconstruct to identical values, those
        # lists should be considered equal for the purpose of detecting state
        # changes (even if the original items are unequal).
        changes = self.get_changes(
            [self.author_name_deconstructible_list_1],
            [self.author_name_deconstructible_list_2],
        )
        self.assertEqual(changes, {})
        # Legitimate differences within the deconstructed lists should be
        # reported as a change
        changes = self.get_changes(
            [self.author_name_deconstructible_list_1],
            [self.author_name_deconstructible_list_3],
        )
        self.assertEqual(len(changes), 1)
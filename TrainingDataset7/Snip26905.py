def test_custom_deconstructible(self):
        """
        Two instances which deconstruct to the same value aren't considered a
        change.
        """
        changes = self.get_changes(
            [self.author_name_deconstructible_1], [self.author_name_deconstructible_2]
        )
        # Right number of migrations?
        self.assertEqual(len(changes), 0)
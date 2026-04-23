def test_unique_together_no_changes(self):
        """
        unique_together doesn't generate a migration if no
        changes have been made.
        """
        changes = self.get_changes(
            [self.author_empty, self.book_unique_together],
            [self.author_empty, self.book_unique_together],
        )
        # Right number of migrations?
        self.assertEqual(len(changes), 0)
def test_unique_together_ordering(self):
        """
        unique_together also triggers on ordering changes.
        """
        changes = self.get_changes(
            [self.author_empty, self.book_unique_together],
            [self.author_empty, self.book_unique_together_2],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(
            changes,
            "otherapp",
            0,
            ["AlterUniqueTogether"],
        )
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            0,
            name="book",
            unique_together={("title", "author")},
        )
def test_remove_unique_together(self):
        """Tests unique_together detection."""
        changes = self.get_changes(
            [self.author_empty, self.book_unique_together],
            [self.author_empty, self.book],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["AlterUniqueTogether"])
        self.assertOperationAttributes(
            changes, "otherapp", 0, 0, name="book", unique_together=set()
        )
def test_remove_indexes(self):
        """Test change detection of removed indexes."""
        changes = self.get_changes(
            [self.author_empty, self.book_indexes], [self.author_empty, self.book]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["RemoveIndex"])
        self.assertOperationAttributes(
            changes, "otherapp", 0, 0, model_name="book", name="book_title_author_idx"
        )
def test_order_fields_indexes(self):
        """Test change detection of reordering of fields in indexes."""
        changes = self.get_changes(
            [self.author_empty, self.book_indexes],
            [self.author_empty, self.book_unordered_indexes],
        )
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["RemoveIndex", "AddIndex"])
        self.assertOperationAttributes(
            changes, "otherapp", 0, 0, model_name="book", name="book_title_author_idx"
        )
        added_index = models.Index(
            fields=["title", "author"], name="book_author_title_idx"
        )
        self.assertOperationAttributes(
            changes, "otherapp", 0, 1, model_name="book", index=added_index
        )
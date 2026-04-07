def test_add_indexes(self):
        """Test change detection of new indexes."""
        changes = self.get_changes(
            [self.author_empty, self.book], [self.author_empty, self.book_indexes]
        )
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["AddIndex"])
        added_index = models.Index(
            fields=["author", "title"], name="book_title_author_idx"
        )
        self.assertOperationAttributes(
            changes, "otherapp", 0, 0, model_name="book", index=added_index
        )
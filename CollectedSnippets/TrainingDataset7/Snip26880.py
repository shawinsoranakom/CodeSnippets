def test_unique_together_remove_fk(self):
        """Tests unique_together and field removal detection & ordering"""
        changes = self.get_changes(
            [self.author_empty, self.book_unique_together],
            [self.author_empty, self.book_with_no_author],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(
            changes,
            "otherapp",
            0,
            ["AlterUniqueTogether", "RemoveField"],
        )
        self.assertOperationAttributes(
            changes, "otherapp", 0, 0, name="book", unique_together=set()
        )
        self.assertOperationAttributes(
            changes, "otherapp", 0, 1, model_name="book", name="author"
        )
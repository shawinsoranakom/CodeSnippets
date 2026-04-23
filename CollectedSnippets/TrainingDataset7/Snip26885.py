def test_remove_field_and_unique_together(self):
        """
        Removed fields will be removed after updating unique_together.
        """
        changes = self.get_changes(
            [self.author_empty, self.book_unique_together_3],
            [self.author_empty, self.book_unique_together],
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
            changes,
            "otherapp",
            0,
            0,
            name="book",
            unique_together={("author", "title")},
        )
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            1,
            model_name="book",
            name="newfield",
        )
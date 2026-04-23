def test_add_field_and_unique_together(self):
        """
        Added fields will be created before using them in unique_together.
        """
        changes = self.get_changes(
            [self.author_empty, self.book],
            [self.author_empty, self.book_unique_together_3],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(
            changes,
            "otherapp",
            0,
            ["AddField", "AlterUniqueTogether"],
        )
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            1,
            name="book",
            unique_together={("title", "newfield")},
        )
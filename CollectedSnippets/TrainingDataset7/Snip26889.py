def test_rename_field_and_unique_together(self):
        """Fields are renamed before updating unique_together."""
        changes = self.get_changes(
            [self.author_empty, self.book_unique_together_3],
            [self.author_empty, self.book_unique_together_4],
            MigrationQuestioner({"ask_rename": True}),
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(
            changes,
            "otherapp",
            0,
            ["RenameField", "AlterUniqueTogether"],
        )
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            1,
            name="book",
            unique_together={("title", "newfield2")},
        )
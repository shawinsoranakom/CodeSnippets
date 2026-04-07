def test_keep_db_table_with_model_change(self):
        """
        Tests when model changes but db_table stays as-is, autodetector must
        not create more than one operation.
        """
        changes = self.get_changes(
            [self.author_with_db_table_options],
            [self.author_renamed_with_db_table_options],
            MigrationQuestioner({"ask_rename_model": True}),
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["RenameModel"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, old_name="Author", new_name="NewAuthor"
        )
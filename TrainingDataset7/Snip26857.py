def test_alter_db_table_comment_remove(self):
        changes = self.get_changes(
            [self.author_with_db_table_comment],
            [self.author_empty],
        )
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterModelTableComment"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="author", db_table_comment=None
        )
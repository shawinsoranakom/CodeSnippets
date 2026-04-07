def test_alter_db_table_comment_add(self):
        changes = self.get_changes(
            [self.author_empty], [self.author_with_db_table_comment]
        )
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterModelTableComment"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="author", table_comment="Table comment"
        )
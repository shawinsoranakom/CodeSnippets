def test_alter_db_table_comment_no_changes(self):
        changes = self.get_changes(
            [self.author_with_db_table_comment],
            [self.author_with_db_table_comment],
        )
        self.assertNumberMigrations(changes, "testapp", 0)
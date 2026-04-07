def test_alter_db_table_comment_change(self):
        author_with_new_db_table_comment = ModelState(
            "testapp",
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
            ],
            {"db_table_comment": "New table comment"},
        )
        changes = self.get_changes(
            [self.author_with_db_table_comment],
            [author_with_new_db_table_comment],
        )
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterModelTableComment"])
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            name="author",
            table_comment="New table comment",
        )
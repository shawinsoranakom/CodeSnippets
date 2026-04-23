def test_rename_model_case(self):
        """
        Model name is case-insensitive. Changing case doesn't lead to any
        autodetected operations.
        """
        author_renamed = ModelState(
            "testapp",
            "author",
            [
                ("id", models.AutoField(primary_key=True)),
            ],
        )
        changes = self.get_changes(
            [self.author_empty, self.book],
            [author_renamed, self.book],
            questioner=MigrationQuestioner({"ask_rename_model": True}),
        )
        self.assertNumberMigrations(changes, "testapp", 0)
        self.assertNumberMigrations(changes, "otherapp", 0)
def test_renamed_referenced_m2m_model_case(self):
        publisher_renamed = ModelState(
            "testapp",
            "publisher",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=100)),
            ],
        )
        changes = self.get_changes(
            [self.publisher, self.author_with_m2m],
            [publisher_renamed, self.author_with_m2m],
            questioner=MigrationQuestioner({"ask_rename_model": True}),
        )
        self.assertNumberMigrations(changes, "testapp", 0)
        self.assertNumberMigrations(changes, "otherapp", 0)
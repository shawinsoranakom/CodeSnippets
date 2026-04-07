def test_rename_referenced_primary_key(self):
        before = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.CharField(primary_key=True, serialize=False)),
                ],
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("foo", models.ForeignKey("app.Foo", models.CASCADE)),
                ],
            ),
        ]
        after = [
            ModelState(
                "app",
                "Foo",
                [("renamed_id", models.CharField(primary_key=True, serialize=False))],
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("foo", models.ForeignKey("app.Foo", models.CASCADE)),
                ],
            ),
        ]
        changes = self.get_changes(
            before, after, MigrationQuestioner({"ask_rename": True})
        )
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["RenameField"])
        self.assertOperationAttributes(
            changes, "app", 0, 0, old_name="id", new_name="renamed_id"
        )
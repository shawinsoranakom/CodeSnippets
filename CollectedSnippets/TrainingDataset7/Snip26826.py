def test_rename_field_foreign_key_to_field(self):
        before = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("field", models.IntegerField(unique=True)),
                ],
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "foo",
                        models.ForeignKey("app.Foo", models.CASCADE, to_field="field"),
                    ),
                ],
            ),
        ]
        after = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("renamed_field", models.IntegerField(unique=True)),
                ],
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "foo",
                        models.ForeignKey(
                            "app.Foo", models.CASCADE, to_field="renamed_field"
                        ),
                    ),
                ],
            ),
        ]
        changes = self.get_changes(
            before, after, MigrationQuestioner({"ask_rename": True})
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["RenameField"])
        self.assertOperationAttributes(
            changes, "app", 0, 0, old_name="field", new_name="renamed_field"
        )
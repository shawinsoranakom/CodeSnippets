def test_rename_field_without_db_column_recreate_constraint(self):
        """Renaming a field without given db_column recreates a constraint."""
        before = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("field", models.IntegerField()),
                ],
                options={
                    "constraints": [
                        models.UniqueConstraint(
                            fields=["field"],
                            name="unique_field",
                        ),
                    ],
                },
            ),
        ]
        after = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "full_field1_name",
                        models.IntegerField(),
                    ),
                ],
                options={
                    "constraints": [
                        models.UniqueConstraint(
                            fields=["full_field1_name"],
                            name="unique_field",
                        ),
                    ],
                },
            ),
        ]
        changes = self.get_changes(
            before, after, MigrationQuestioner({"ask_rename": True})
        )
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(
            changes, "app", 0, ["RemoveConstraint", "RenameField", "AddConstraint"]
        )
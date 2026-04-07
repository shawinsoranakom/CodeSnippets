def test_rename_field_preserve_db_column_recreate_constraint(self):
        """Removing a field from the constraint triggers recreation."""
        before = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("field1", models.IntegerField(db_column="field1")),
                    ("field2", models.IntegerField(db_column="field2")),
                ],
                options={
                    "constraints": [
                        models.UniqueConstraint(
                            fields=["field1", "field2"],
                            name="unique_fields",
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
                    ("renamed_field1", models.IntegerField(db_column="field1")),
                    ("renamed_field2", models.IntegerField(db_column="field2")),
                ],
                options={
                    "constraints": [
                        models.UniqueConstraint(
                            fields=["renamed_field1"],
                            name="unique_fields",
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
            changes,
            "app",
            0,
            [
                "RemoveConstraint",
                "RenameField",
                "RenameField",
                "AddConstraint",
            ],
        )
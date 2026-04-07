def test_rename_related_field_preserved_db_column(self):
        before = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
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
                [
                    ("id", models.AutoField(primary_key=True)),
                ],
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "renamed_foo",
                        models.ForeignKey(
                            "app.Foo", models.CASCADE, db_column="foo_id"
                        ),
                    ),
                ],
            ),
        ]
        changes = self.get_changes(
            before, after, MigrationQuestioner({"ask_rename": True})
        )
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["AlterField", "RenameField"])
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            0,
            model_name="bar",
            name="foo",
        )
        self.assertEqual(
            changes["app"][0].operations[0].field.deconstruct(),
            (
                "foo",
                "django.db.models.ForeignKey",
                [],
                {"to": "app.foo", "on_delete": models.CASCADE, "db_column": "foo_id"},
            ),
        )
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            1,
            model_name="bar",
            old_name="foo",
            new_name="renamed_foo",
        )
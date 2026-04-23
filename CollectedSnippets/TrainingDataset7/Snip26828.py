def test_rename_foreign_object_fields(self):
        fields = ("first", "second")
        renamed_fields = ("first_renamed", "second_renamed")
        before = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("first", models.IntegerField()),
                    ("second", models.IntegerField()),
                ],
                options={"unique_together": {fields}},
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("first", models.IntegerField()),
                    ("second", models.IntegerField()),
                    (
                        "foo",
                        models.ForeignObject(
                            "app.Foo",
                            models.CASCADE,
                            from_fields=fields,
                            to_fields=fields,
                        ),
                    ),
                ],
            ),
        ]
        # Case 1: to_fields renames.
        after = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("first_renamed", models.IntegerField()),
                    ("second_renamed", models.IntegerField()),
                ],
                options={"unique_together": {renamed_fields}},
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("first", models.IntegerField()),
                    ("second", models.IntegerField()),
                    (
                        "foo",
                        models.ForeignObject(
                            "app.Foo",
                            models.CASCADE,
                            from_fields=fields,
                            to_fields=renamed_fields,
                        ),
                    ),
                ],
            ),
        ]
        changes = self.get_changes(
            before, after, MigrationQuestioner({"ask_rename": True})
        )
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(
            changes, "app", 0, ["RenameField", "RenameField", "AlterUniqueTogether"]
        )
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            0,
            model_name="foo",
            old_name="first",
            new_name="first_renamed",
        )
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            1,
            model_name="foo",
            old_name="second",
            new_name="second_renamed",
        )
        # Case 2: from_fields renames.
        after = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("first", models.IntegerField()),
                    ("second", models.IntegerField()),
                ],
                options={"unique_together": {fields}},
            ),
            ModelState(
                "app",
                "Bar",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("first_renamed", models.IntegerField()),
                    ("second_renamed", models.IntegerField()),
                    (
                        "foo",
                        models.ForeignObject(
                            "app.Foo",
                            models.CASCADE,
                            from_fields=renamed_fields,
                            to_fields=fields,
                        ),
                    ),
                ],
            ),
        ]
        changes = self.get_changes(
            before, after, MigrationQuestioner({"ask_rename": True})
        )
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["RenameField", "RenameField"])
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            0,
            model_name="bar",
            old_name="first",
            new_name="first_renamed",
        )
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            1,
            model_name="bar",
            old_name="second",
            new_name="second_renamed",
        )
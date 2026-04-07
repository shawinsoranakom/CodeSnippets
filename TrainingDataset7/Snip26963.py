def test_does_not_crash_after_rename_on_unique_together(self):
        fields = ("first", "second")
        before = self.make_project_state(
            [
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
            ]
        )
        after = before.clone()
        after.rename_field("app", "foo", "first", "first_renamed")

        changes = MigrationAutodetector(
            before, after, MigrationQuestioner({"ask_rename": True})
        )._detect_changes()

        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(
            changes, "app", 0, ["RenameField", "AlterUniqueTogether"]
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
            name="foo",
            unique_together={("first_renamed", "second")},
        )
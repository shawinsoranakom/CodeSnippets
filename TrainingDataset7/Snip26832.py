def test_rename_field_preserve_db_column_preserve_constraint(self):
        """
        Renaming a field that already had a db_column attribute and a
        constraint generates two no-op operations: RenameField and
        AlterConstraint.
        """
        before = [
            ModelState(
                "app",
                "Foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("field", models.IntegerField(db_column="full_field1_name")),
                    ("field2", models.IntegerField()),
                ],
                options={
                    "constraints": [
                        models.UniqueConstraint(
                            fields=["field", "field2"],
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
                        models.IntegerField(db_column="full_field1_name"),
                    ),
                    (
                        "field2",
                        models.IntegerField(),
                    ),
                ],
                options={
                    "constraints": [
                        models.UniqueConstraint(
                            fields=["full_field1_name", "field2"],
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
        self.assertOperationTypes(changes, "app", 0, ["RenameField", "AlterConstraint"])
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            1,
            model_name="foo",
            name="unique_field",
        )
        self.assertEqual(
            changes["app"][0].operations[1].deconstruct(),
            (
                "AlterConstraint",
                [],
                {
                    "constraint": after[0].options["constraints"][0],
                    "model_name": "foo",
                    "name": "unique_field",
                },
            ),
        )
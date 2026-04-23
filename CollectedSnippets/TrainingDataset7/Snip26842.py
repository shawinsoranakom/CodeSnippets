def test_rename_model_reverse_relation_dependencies(self):
        """
        The migration to rename a model pointed to by a foreign key in another
        app must run after the other app's migration that adds the foreign key
        with model's original name. Therefore, the renaming migration has a
        dependency on that other migration.
        """
        before = [
            ModelState(
                "testapp",
                "EntityA",
                [
                    ("id", models.AutoField(primary_key=True)),
                ],
            ),
            ModelState(
                "otherapp",
                "EntityB",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("entity_a", models.ForeignKey("testapp.EntityA", models.CASCADE)),
                ],
            ),
        ]
        after = [
            ModelState(
                "testapp",
                "RenamedEntityA",
                [
                    ("id", models.AutoField(primary_key=True)),
                ],
            ),
            ModelState(
                "otherapp",
                "EntityB",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "entity_a",
                        models.ForeignKey("testapp.RenamedEntityA", models.CASCADE),
                    ),
                ],
            ),
        ]
        changes = self.get_changes(
            before, after, MigrationQuestioner({"ask_rename_model": True})
        )
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertMigrationDependencies(
            changes, "testapp", 0, [("otherapp", "__first__")]
        )
        self.assertOperationTypes(changes, "testapp", 0, ["RenameModel"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, old_name="EntityA", new_name="RenamedEntityA"
        )
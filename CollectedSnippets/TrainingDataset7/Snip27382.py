def test_rename_field_with_db_column(self):
        project_state = self.apply_operations(
            "test_rfwdbc",
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "Pony",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("field", models.IntegerField(db_column="db_field")),
                        (
                            "fk_field",
                            models.ForeignKey(
                                "Pony",
                                models.CASCADE,
                                db_column="db_fk_field",
                            ),
                        ),
                    ],
                ),
            ],
        )
        new_state = project_state.clone()
        operation = migrations.RenameField("Pony", "field", "renamed_field")
        operation.state_forwards("test_rfwdbc", new_state)
        self.assertIn("renamed_field", new_state.models["test_rfwdbc", "pony"].fields)
        self.assertNotIn("field", new_state.models["test_rfwdbc", "pony"].fields)
        self.assertColumnExists("test_rfwdbc_pony", "db_field")
        with connection.schema_editor() as editor:
            with self.assertNumQueries(0):
                operation.database_forwards(
                    "test_rfwdbc", editor, project_state, new_state
                )
        self.assertColumnExists("test_rfwdbc_pony", "db_field")
        with connection.schema_editor() as editor:
            with self.assertNumQueries(0):
                operation.database_backwards(
                    "test_rfwdbc", editor, new_state, project_state
                )
        self.assertColumnExists("test_rfwdbc_pony", "db_field")

        new_state = project_state.clone()
        operation = migrations.RenameField("Pony", "fk_field", "renamed_fk_field")
        operation.state_forwards("test_rfwdbc", new_state)
        self.assertIn(
            "renamed_fk_field", new_state.models["test_rfwdbc", "pony"].fields
        )
        self.assertNotIn("fk_field", new_state.models["test_rfwdbc", "pony"].fields)
        self.assertColumnExists("test_rfwdbc_pony", "db_fk_field")
        with connection.schema_editor() as editor:
            with self.assertNumQueries(0):
                operation.database_forwards(
                    "test_rfwdbc", editor, project_state, new_state
                )
        self.assertColumnExists("test_rfwdbc_pony", "db_fk_field")
        with connection.schema_editor() as editor:
            with self.assertNumQueries(0):
                operation.database_backwards(
                    "test_rfwdbc", editor, new_state, project_state
                )
        self.assertColumnExists("test_rfwdbc_pony", "db_fk_field")
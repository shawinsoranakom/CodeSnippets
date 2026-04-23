def test_rename_field_case(self):
        project_state = self.apply_operations(
            "test_rfmx",
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "Pony",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("field", models.IntegerField()),
                    ],
                ),
            ],
        )
        new_state = project_state.clone()
        operation = migrations.RenameField("Pony", "field", "FiElD")
        operation.state_forwards("test_rfmx", new_state)
        self.assertIn("FiElD", new_state.models["test_rfmx", "pony"].fields)
        self.assertColumnExists("test_rfmx_pony", "field")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_rfmx", editor, project_state, new_state)
        self.assertColumnExists(
            "test_rfmx_pony",
            connection.introspection.identifier_converter("FiElD"),
        )
        with connection.schema_editor() as editor:
            operation.database_backwards("test_rfmx", editor, new_state, project_state)
        self.assertColumnExists("test_rfmx_pony", "field")
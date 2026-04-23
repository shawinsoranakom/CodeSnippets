def test_alter_model_table_comment(self):
        app_label = "test_almotaco"
        project_state = self.set_up_test_model(app_label)
        pony_table = f"{app_label}_pony"
        # Add table comment.
        operation = migrations.AlterModelTableComment("Pony", "Custom pony comment")
        self.assertEqual(operation.describe(), "Alter Pony table comment")
        self.assertEqual(
            operation.formatted_description(), "~ Alter Pony table comment"
        )
        self.assertEqual(operation.migration_name_fragment, "alter_pony_table_comment")
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(
            new_state.models[app_label, "pony"].options["db_table_comment"],
            "Custom pony comment",
        )
        self.assertTableCommentNotExists(pony_table)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertTableComment(pony_table, "Custom pony comment")
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertTableCommentNotExists(pony_table)
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterModelTableComment")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2], {"name": "Pony", "table_comment": "Custom pony comment"}
        )
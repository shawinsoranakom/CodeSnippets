def test_alter_field_pk_mti_and_fk_to_base(self):
        app_label = "test_alflpkmtiftb"
        project_state = self.set_up_test_model(
            app_label,
            mti_model=True,
            related_model=True,
        )
        operation = migrations.AlterField(
            "Pony",
            "id",
            models.BigAutoField(primary_key=True),
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertIsInstance(
            new_state.models[app_label, "pony"].fields["id"],
            models.BigAutoField,
        )

        def _get_column_id_type(cursor, table, column):
            return [
                c.type_code
                for c in connection.introspection.get_table_description(
                    cursor,
                    f"{app_label}_{table}",
                )
                if c.name == column
            ][0]

        def assertIdTypeEqualsMTIFkType():
            with connection.cursor() as cursor:
                parent_id_type = _get_column_id_type(cursor, "pony", "id")
                fk_id_type = _get_column_id_type(cursor, "rider", "pony_id")
                child_id_type = _get_column_id_type(
                    cursor, "shetlandpony", "pony_ptr_id"
                )
            self.assertEqual(parent_id_type, child_id_type)
            self.assertEqual(parent_id_type, fk_id_type)

        assertIdTypeEqualsMTIFkType()
        # Alter primary key.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        assertIdTypeEqualsMTIFkType()
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                f"{app_label}_shetlandpony",
                ["pony_ptr_id"],
                (f"{app_label}_pony", "id"),
            )
            self.assertFKExists(
                f"{app_label}_rider",
                ["pony_id"],
                (f"{app_label}_pony", "id"),
            )
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        assertIdTypeEqualsMTIFkType()
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                f"{app_label}_shetlandpony",
                ["pony_ptr_id"],
                (f"{app_label}_pony", "id"),
            )
            self.assertFKExists(
                f"{app_label}_rider",
                ["pony_id"],
                (f"{app_label}_pony", "id"),
            )
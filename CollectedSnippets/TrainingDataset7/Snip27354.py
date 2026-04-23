def test_alter_model_table_m2m(self):
        """
        AlterModelTable should rename auto-generated M2M tables.
        """
        app_label = "test_talflmltlm2m"
        pony_db_table = "pony_foo"
        project_state = self.set_up_test_model(
            app_label, second_model=True, db_table=pony_db_table
        )
        # Add the M2M field
        first_state = project_state.clone()
        operation = migrations.AddField(
            "Pony", "stables", models.ManyToManyField("Stable")
        )
        operation.state_forwards(app_label, first_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, first_state)
        original_m2m_table = "%s_%s" % (pony_db_table, "stables")
        new_m2m_table = "%s_%s" % (app_label, "pony_stables")
        self.assertTableExists(original_m2m_table)
        self.assertTableNotExists(new_m2m_table)
        # Rename the Pony db_table which should also rename the m2m table.
        second_state = first_state.clone()
        operation = migrations.AlterModelTable(name="pony", table=None)
        operation.state_forwards(app_label, second_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, first_state, second_state)
        self.assertTableExists(new_m2m_table)
        self.assertTableNotExists(original_m2m_table)
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, second_state, first_state)
        self.assertTableExists(original_m2m_table)
        self.assertTableNotExists(new_m2m_table)
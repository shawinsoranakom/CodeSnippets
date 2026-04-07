def test_alter_field_pk(self):
        """
        The AlterField operation on primary keys (things like PostgreSQL's
        SERIAL weirdness).
        """
        project_state = self.set_up_test_model("test_alflpk")
        # Test the state alteration
        operation = migrations.AlterField(
            "Pony", "id", models.IntegerField(primary_key=True)
        )
        new_state = project_state.clone()
        operation.state_forwards("test_alflpk", new_state)
        self.assertIsInstance(
            project_state.models["test_alflpk", "pony"].fields["id"],
            models.AutoField,
        )
        self.assertIsInstance(
            new_state.models["test_alflpk", "pony"].fields["id"],
            models.IntegerField,
        )
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards("test_alflpk", editor, project_state, new_state)
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_alflpk", editor, new_state, project_state
            )
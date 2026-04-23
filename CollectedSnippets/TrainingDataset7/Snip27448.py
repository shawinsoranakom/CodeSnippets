def test_separate_database_and_state2(self):
        """
        A complex SeparateDatabaseAndState operation: Multiple operations both
        for state and database. Verify the state dependencies within each list
        and that state ops don't affect the database.
        """
        app_label = "test_separatedatabaseandstate2"
        project_state = self.set_up_test_model(app_label)
        # Create the operation
        database_operations = [
            migrations.CreateModel(
                "ILovePonies",
                [("id", models.AutoField(primary_key=True))],
                options={"db_table": "iloveponies"},
            ),
            migrations.CreateModel(
                "ILoveMorePonies",
                # We use IntegerField and not AutoField because
                # the model is going to be deleted immediately
                # and with an AutoField this fails on Oracle
                [("id", models.IntegerField(primary_key=True))],
                options={"db_table": "ilovemoreponies"},
            ),
            migrations.DeleteModel("ILoveMorePonies"),
            migrations.CreateModel(
                "ILoveEvenMorePonies",
                [("id", models.AutoField(primary_key=True))],
                options={"db_table": "iloveevenmoreponies"},
            ),
        ]
        state_operations = [
            migrations.CreateModel(
                "SomethingElse",
                [("id", models.AutoField(primary_key=True))],
                options={"db_table": "somethingelse"},
            ),
            migrations.DeleteModel("SomethingElse"),
            migrations.CreateModel(
                "SomethingCompletelyDifferent",
                [("id", models.AutoField(primary_key=True))],
                options={"db_table": "somethingcompletelydifferent"},
            ),
        ]
        operation = migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=database_operations,
        )
        # Test the state alteration
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)

        def assertModelsAndTables(after_db):
            # Tables and models exist, or don't, as they should:
            self.assertNotIn((app_label, "somethingelse"), new_state.models)
            self.assertEqual(
                len(new_state.models[app_label, "somethingcompletelydifferent"].fields),
                1,
            )
            self.assertNotIn((app_label, "iloveponiesonies"), new_state.models)
            self.assertNotIn((app_label, "ilovemoreponies"), new_state.models)
            self.assertNotIn((app_label, "iloveevenmoreponies"), new_state.models)
            self.assertTableNotExists("somethingelse")
            self.assertTableNotExists("somethingcompletelydifferent")
            self.assertTableNotExists("ilovemoreponies")
            if after_db:
                self.assertTableExists("iloveponies")
                self.assertTableExists("iloveevenmoreponies")
            else:
                self.assertTableNotExists("iloveponies")
                self.assertTableNotExists("iloveevenmoreponies")

        assertModelsAndTables(after_db=False)
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        assertModelsAndTables(after_db=True)
        # And test reversal
        self.assertTrue(operation.reversible)
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        assertModelsAndTables(after_db=False)
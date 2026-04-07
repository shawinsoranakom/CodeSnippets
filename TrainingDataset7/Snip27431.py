def test_run_sql(self):
        """
        Tests the RunSQL operation.
        """
        project_state = self.set_up_test_model("test_runsql")
        # Create the operation
        operation = migrations.RunSQL(
            # Use a multi-line string with a comment to test splitting on
            # SQLite and MySQL respectively.
            "CREATE TABLE i_love_ponies (id int, special_thing varchar(15));\n"
            "INSERT INTO i_love_ponies (id, special_thing) "
            "VALUES (1, 'i love ponies'); -- this is magic!\n"
            "INSERT INTO i_love_ponies (id, special_thing) "
            "VALUES (2, 'i love django');\n"
            "UPDATE i_love_ponies SET special_thing = 'Ponies' "
            "WHERE special_thing LIKE '%%ponies';"
            "UPDATE i_love_ponies SET special_thing = 'Django' "
            "WHERE special_thing LIKE '%django';",
            # Run delete queries to test for parameter substitution failure
            # reported in #23426
            "DELETE FROM i_love_ponies WHERE special_thing LIKE '%Django%';"
            "DELETE FROM i_love_ponies WHERE special_thing LIKE '%%Ponies%%';"
            "DROP TABLE i_love_ponies",
            state_operations=[
                migrations.CreateModel(
                    "SomethingElse", [("id", models.AutoField(primary_key=True))]
                )
            ],
        )
        self.assertEqual(operation.describe(), "Raw SQL operation")
        self.assertEqual(operation.formatted_description(), "s Raw SQL operation")
        # Test the state alteration
        new_state = project_state.clone()
        operation.state_forwards("test_runsql", new_state)
        self.assertEqual(
            len(new_state.models["test_runsql", "somethingelse"].fields), 1
        )
        # Make sure there's no table
        self.assertTableNotExists("i_love_ponies")
        # Test SQL collection
        with connection.schema_editor(collect_sql=True) as editor:
            operation.database_forwards("test_runsql", editor, project_state, new_state)
            self.assertIn("LIKE '%%ponies';", "\n".join(editor.collected_sql))
            operation.database_backwards(
                "test_runsql", editor, project_state, new_state
            )
            self.assertIn("LIKE '%%Ponies%%';", "\n".join(editor.collected_sql))
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards("test_runsql", editor, project_state, new_state)
        self.assertTableExists("i_love_ponies")
        # Make sure all the SQL was processed
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM i_love_ponies")
            self.assertEqual(cursor.fetchall()[0][0], 2)
            cursor.execute(
                "SELECT COUNT(*) FROM i_love_ponies WHERE special_thing = 'Django'"
            )
            self.assertEqual(cursor.fetchall()[0][0], 1)
            cursor.execute(
                "SELECT COUNT(*) FROM i_love_ponies WHERE special_thing = 'Ponies'"
            )
            self.assertEqual(cursor.fetchall()[0][0], 1)
        # And test reversal
        self.assertTrue(operation.reversible)
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_runsql", editor, new_state, project_state
            )
        self.assertTableNotExists("i_love_ponies")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RunSQL")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            sorted(definition[2]), ["reverse_sql", "sql", "state_operations"]
        )
        # And elidable reduction
        self.assertIs(False, operation.reduce(operation, []))
        elidable_operation = migrations.RunSQL("SELECT 1 FROM void;", elidable=True)
        self.assertEqual(elidable_operation.reduce(operation, []), [operation])

        # Test elidable deconstruction
        definition = elidable_operation.deconstruct()
        self.assertIs(definition[2]["elidable"], True)
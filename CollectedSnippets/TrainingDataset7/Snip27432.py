def test_run_sql_params(self):
        """
        #23426 - RunSQL should accept parameters.
        """
        project_state = self.set_up_test_model("test_runsql")
        # Create the operation
        operation = migrations.RunSQL(
            ["CREATE TABLE i_love_ponies (id int, special_thing varchar(15));"],
            ["DROP TABLE i_love_ponies"],
        )
        param_operation = migrations.RunSQL(
            # forwards
            (
                "INSERT INTO i_love_ponies (id, special_thing) VALUES (1, 'Django');",
                [
                    "INSERT INTO i_love_ponies (id, special_thing) VALUES (2, %s);",
                    ["Ponies"],
                ],
                (
                    "INSERT INTO i_love_ponies (id, special_thing) VALUES (%s, %s);",
                    (
                        3,
                        "Python",
                    ),
                ),
            ),
            # backwards
            [
                "DELETE FROM i_love_ponies WHERE special_thing = 'Django';",
                ["DELETE FROM i_love_ponies WHERE special_thing = 'Ponies';", None],
                (
                    "DELETE FROM i_love_ponies WHERE id = %s OR special_thing = %s;",
                    [3, "Python"],
                ),
            ],
        )

        # Make sure there's no table
        self.assertTableNotExists("i_love_ponies")
        new_state = project_state.clone()
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards("test_runsql", editor, project_state, new_state)

        # Test parameter passing
        with connection.schema_editor() as editor:
            param_operation.database_forwards(
                "test_runsql", editor, project_state, new_state
            )
        # Make sure all the SQL was processed
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM i_love_ponies")
            self.assertEqual(cursor.fetchall()[0][0], 3)

        with connection.schema_editor() as editor:
            param_operation.database_backwards(
                "test_runsql", editor, new_state, project_state
            )
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM i_love_ponies")
            self.assertEqual(cursor.fetchall()[0][0], 0)

        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_runsql", editor, new_state, project_state
            )
        self.assertTableNotExists("i_love_ponies")
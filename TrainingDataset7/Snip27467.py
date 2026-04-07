def test_add_field_ignore_swapped(self):
        """
        Tests the AddField operation.
        """
        # Test the state alteration
        operation = migrations.AddField(
            "Pony",
            "height",
            models.FloatField(null=True, default=5),
        )
        project_state, new_state = self.make_test_state("test_adfligsw", operation)
        # Test the database alteration
        self.assertTableNotExists("test_adfligsw_pony")
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_adfligsw", editor, project_state, new_state
            )
        self.assertTableNotExists("test_adfligsw_pony")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_adfligsw", editor, new_state, project_state
            )
        self.assertTableNotExists("test_adfligsw_pony")
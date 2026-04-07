def test_nonexistent_fixture_no_constraint_checking(
        self, disable_constraint_checking, enable_constraint_checking
    ):
        """
        If no fixtures match the loaddata command, constraints checks on the
        database shouldn't be disabled. This is performance critical on MSSQL.
        """
        with self.assertRaisesMessage(
            CommandError, "No fixture named 'this_fixture_doesnt_exist' found."
        ):
            management.call_command(
                "loaddata", "this_fixture_doesnt_exist", verbosity=0
            )
        disable_constraint_checking.assert_not_called()
        enable_constraint_checking.assert_not_called()
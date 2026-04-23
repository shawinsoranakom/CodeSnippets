def test_loaddata_not_existent_fixture_file(self):
        stdout_output = StringIO()
        with self.assertRaisesMessage(
            CommandError, "No fixture named 'this_fixture_doesnt_exist' found."
        ):
            management.call_command(
                "loaddata", "this_fixture_doesnt_exist", stdout=stdout_output
            )
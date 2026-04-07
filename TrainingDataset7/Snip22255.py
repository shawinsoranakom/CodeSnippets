def test_loaddata_no_fixture_specified(self):
        """
        Error is quickly reported when no fixtures is provided in the command
        line.
        """
        msg = (
            "No database fixture specified. Please provide the path of at least one "
            "fixture in the command line."
        )
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command(
                "loaddata",
                verbosity=0,
            )
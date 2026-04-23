def test_not_supported(self):
        msg = (
            "Database inspection isn't supported for the currently selected "
            "database backend."
        )
        with self.assertRaisesMessage(CommandError, msg):
            call_command("inspectdb")
def test_non_existent_command_output(self):
        out, err = self.run_manage(
            ["invalid_command"], manage_py="configured_settings_manage.py"
        )
        self.assertNoOutput(out)
        self.assertOutput(err, "Unknown command: 'invalid_command'")
        self.assertNotInOutput(err, "No Django settings specified")
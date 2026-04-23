def test_stdin_without_format(self):
        """Reading from stdin raises an error if format isn't specified."""
        msg = "--format must be specified when reading from stdin."
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command("loaddata", "-", verbosity=0)
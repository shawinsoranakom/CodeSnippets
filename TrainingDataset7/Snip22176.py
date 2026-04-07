def test_ambiguous_compressed_fixture(self):
        # The name "fixture5" is ambiguous, so loading raises an error.
        msg = "Multiple fixtures named 'fixture5'"
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command("loaddata", "fixture5", verbosity=0)
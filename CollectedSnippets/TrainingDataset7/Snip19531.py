def test_fail_level(self):
        with self.assertRaises(CommandError):
            call_command("check", fail_level="WARNING")
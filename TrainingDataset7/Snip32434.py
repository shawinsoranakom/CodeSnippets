def test_missing_args_message(self):
        msg = "Enter at least one staticfile."
        with self.assertRaisesMessage(CommandError, msg):
            call_command("findstatic")
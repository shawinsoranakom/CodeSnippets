def test_missing_receivers(self):
        """
        The command should complain if no receivers are given (and --admins or
        --managers are not set).
        """
        msg = (
            "You must specify some email recipients, or pass the --managers or "
            "--admin options."
        )
        with self.assertRaisesMessage(CommandError, msg):
            call_command("sendtestemail")
def test_makemigrations_empty_no_app_specified(self):
        """
        makemigrations exits if no app is specified with 'empty' mode.
        """
        msg = "You must supply at least one app label when using --empty."
        with self.assertRaisesMessage(CommandError, msg):
            call_command("makemigrations", empty=True)
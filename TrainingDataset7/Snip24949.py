def test_error_reported_by_msgfmt(self):
        # po file contains wrong po formatting.
        with self.assertRaises(CommandError):
            call_command("compilemessages", locale=["ja"], verbosity=0)
        # It should still fail a second time.
        with self.assertRaises(CommandError):
            call_command("compilemessages", locale=["ja"], verbosity=0)
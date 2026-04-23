def test_invalid_tag(self):
        msg = 'There is no system check with the "missingtag" tag.'
        with self.assertRaisesMessage(CommandError, msg):
            call_command("check", tags=["missingtag"])